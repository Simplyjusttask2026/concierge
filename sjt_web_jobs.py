"""Install fail-closed owner routes and observable, idempotent jobs."""
import datetime as dt
import json
import os
import threading
from sjt_reliability import (authorized, enabled, configured_state, daily,
    now_et, report_mail, response_error)


def config(ns):
    return {'crm_writes': enabled('SJT_ENABLE_CRM_WRITES'),
            'outreach_enabled': enabled('SJT_ENABLE_OUTREACH'),
            'reports_enabled': enabled('SJT_ENABLE_REPORT_EMAIL'),
            'social_enabled': enabled('SJT_ENABLE_SOCIAL_POSTS'),
            'daily_cap': min(10, max(0, int(os.environ.get('OUTREACH_DAILY_CAP', '10')))),
            'mail_account': ns['ZOHO_MAIL_ACCOUNT_ID'], 'mail_from': ns['ZOHO_FROM'],
            'report_email': ns['REPORT_EMAIL'], 'report_cc': ns['REPORT_CC']}


def provider_id(resp):
    for _ in range(5):
        if response_error(resp):
            return ''
        if resp.get('post_id') or resp.get('id'):
            return str(resp.get('post_id') or resp.get('id'))
        resp = resp.get('data')
        if not isinstance(resp, dict):
            return ''
    return ''


def social(ns, state, cfg):
    today = now_et().date().isoformat()
    svc = ns['SOCIAL_SERVICES'][now_et().date().toordinal() % len(ns['SOCIAL_SERVICES'])]
    caption = (svc[1] + '\nSimply Just Task helps busy families, homeowners and seniors in '
               'Apopka and Central Florida with ' + svc[0].lower() + '.\n'
               'Call/text Anthony Quinones (352) 849-2344 or Michael Sabo (321) 745-5894 '
               '- or email tasksupport@simplyjusttask.com')
    report = {'mode': 'apply' if cfg['social_enabled'] else 'read_only',
              'caption': caption, 'outcomes': [], 'errors': []}
    if not cfg['social_enabled']:
        report['outcomes'].append({'status': 'held_social_disabled'})
        return report
    if not 8 <= now_et().hour < 21:
        report['outcomes'].append({'status': 'held_quiet_hours'})
        return report
    execute = ns['_social_exec']
    # No paid generators, synthetic before/after, scraped private images or external image fallback.
    # Instagram is held unless the owner explicitly supplies an approved real JPEG.
    image = os.environ.get('SJT_APPROVED_REAL_IMAGE_URL', '').strip()
    if image and (not image.startswith('https://') or not enabled('SJT_REAL_IMAGE_APPROVED')):
        report['errors'].append('owner-approved HTTPS real image required')
        return report
    for platform in ('facebook', 'instagram'):
        if platform == 'instagram' and not image:
            report['outcomes'].append({'platform': platform, 'status': 'held_real_image_required'})
            continue
        key = platform+':'+today
        claimed = state.reserve_delivery(key, today, 1, platform)
        if claimed != 'reserved':
            report['outcomes'].append({'platform': platform, 'status': claimed})
            continue
        try:
            if platform == 'facebook':
                slug = 'FACEBOOK_CREATE_PHOTO_POST' if image else 'FACEBOOK_CREATE_POST'
                args = {'page_id': ns['SOCIAL_FB_PAGE_ID'], 'message': caption, 'published': True}
                if image:
                    args['url'] = image
                result = execute(slug, args)
            else:
                container = execute('INSTAGRAM_POST_IG_USER_MEDIA', {
                    'ig_user_id': ns['SOCIAL_IG_USER_ID'], 'image_url': image, 'caption': caption})
                cid = provider_id(container)
                if not cid:
                    raise RuntimeError('container not acknowledged')
                result = execute('INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH', {
                    'ig_user_id': ns['SOCIAL_IG_USER_ID'], 'creation_id': cid, 'max_wait_seconds': 120})
            ident = provider_id(result)
            state.delivered(key, 'provider_accepted' if ident else 'uncertain', ident)
            report['outcomes'].append({'platform': platform,
                'status': 'provider_accepted' if ident else 'uncertain_do_not_retry', 'provider_id': ident})
        except Exception:
            state.delivered(key, 'uncertain')
            report['errors'].append(platform+': uncertain; inspect provider before any retry')
    # Do not give an unrestricted autonomous agent all social tools during a repair run.
    report['inbox_replies'] = 'held_pending_verified_read_and_approval_adapter'
    return report


def install(app, ns):
    from flask import request, jsonify
    app.config['MAX_CONTENT_LENGTH'] = 32768
    protected = {'/run-daily', '/run-social', '/sync-cal-bookings', '/call-center',
        '/debug', '/zoho-direct-test', '/zoho-token-helper', '/composio-zoho-connect',
        '/composio-zoho-connected', '/ingest-crewai-leads', '/crewai-task-webhook'}

    @app.before_request
    def owner_only():
        if request.path in protected or request.path.startswith('/ops/'):
            token = os.environ.get('MACHINE_TOKEN', '')
            if not token:
                return jsonify({'error': 'owner token not configured; refusing access'}), 503
            if not authorized(token, request.headers.get('x-machine-token', '')):
                return jsonify({'error': 'unauthorized'}), 401
            if request.path in ('/run-daily', '/run-social') and request.method != 'POST':
                return jsonify({'error': 'POST required; no job started'}), 405

    def submit(kind):
        try:
            state = configured_state()
        except Exception:
            return jsonify({'error': 'persistent job state not configured; no job started'}), 503
        cfg = config(ns)
        mode = 'apply' if ((kind == 'daily' and cfg['crm_writes']) or
                           (kind == 'social' and cfg['social_enabled'])) else 'read_only'
        # Server chooses the key: repeated/manual HTTP requests cannot bypass the daily claim.
        key = kind+':'+now_et().date().isoformat()+':'+mode
        ident, claimed = state.claim_job(key, kind)
        if not claimed:
            return jsonify({'job_id': ident, 'duplicate': True, 'status': state.job(ident)['status']}), 200

        def worker():
            state.finish(ident, 'running', {'mode': mode})
            try:
                if kind == 'daily':
                    result = daily(ns['zoho_exec'], ns['_llm_json'], ns['QUALIFY_PROMPT'],
                                   ns['OUTREACH_PROMPT'], state, cfg)
                    if cfg['crm_writes']:
                        result['cal_sync'] = ns['_sync_recent_cal_bookings']()
                        result['errors'].extend(result['cal_sync'].get('errors') or [])
                else:
                    result = social(ns, state, cfg)
                # Persist work result BEFORE attempting owner email: report delivery cannot erase it.
                state.finish(ident, 'reporting', result)
                if mode == 'apply':
                    result['report_delivery'] = report_mail(ns['zoho_exec'], state, result, cfg, 'report:'+ident)
                held = any(str(x.get('status','')).startswith(('held_', 'uncertain'))
                           for x in result.get('outcomes', []))
                mail = result.get('report_delivery', {}).get('status')
                if mode == 'read_only':
                    status = 'succeeded_read_only'
                elif result.get('errors') or held or mail != 'provider_accepted':
                    status = 'partial'
                else:
                    status = 'succeeded'
                state.finish(ident, status, result)
            except Exception as exc:
                state.finish(ident, 'failed', {'mode': mode, 'error': type(exc).__name__,
                    'note': 'No automatic retry. Review provider and durable ledger before recovery.'})
        threading.Thread(target=worker, daemon=True).start()
        return jsonify({'job_id': ident, 'status': 'queued', 'mode': mode,
                        'completion_url': '/ops/jobs/'+ident}), 202

    @app.route('/ops/jobs/<ident>', methods=['GET'])
    def job_status(ident):
        try:
            result = configured_state().job(ident)
        except Exception:
            return jsonify({'error': 'job state unavailable'}), 503
        return (jsonify(result), 200) if result else (jsonify({'error': 'not found'}), 404)

    @app.route('/ops/jobs', methods=['GET'])
    def recent_jobs():
        try:
            state = configured_state()
            with state.connect() as c:
                rows = c.execute('SELECT id,kind,status,created FROM jobs ORDER BY created DESC LIMIT 50').fetchall()
            return jsonify({'jobs': [dict(r) for r in rows]})
        except Exception:
            return jsonify({'error': 'job state unavailable'}), 503

    app.view_functions['run_daily'] = lambda: submit('daily')
    app.view_functions['run_social'] = lambda: submit('social')
