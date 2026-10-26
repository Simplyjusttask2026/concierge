import pathlib
p = pathlib.Path('concierge.py')
s = p.read_text()
if 'social-auto-v1' in s:
    print('Already patched')
    raise SystemExit(0)
old_platforms = 'SOCIAL_PLATFORMS = ["facebook", "instagram", "twitter"]'
assert old_platforms in s, 'platforms anchor missing'
s = s.replace(old_platforms, 'SOCIAL_PLATFORMS = ["facebook", "instagram"]  # social-auto-v1 daily AI photo post', 1)
start = s.index('def run_social_pipeline():')
end_marker = '# ================= CREWAI STUDIO -> ZOHO BRIDGE ================='
end = s.index(end_marker)
NEW = r'''
def _social_exec(slug, args):
    try:
        resp = composio.tools.execute(slug=slug, arguments=args, user_id=COMPOSIO_USER_ID, dangerously_skip_version_check=True)
    except TypeError:
        try:
            resp = composio.tools.execute(slug, args, COMPOSIO_USER_ID)
        except Exception as e:
            return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}
    if isinstance(resp, dict):
        return resp
    for meth in ('model_dump', 'dict'):
        fn = getattr(resp, meth, None)
        if callable(fn):
            try:
                v = fn()
                if isinstance(v, dict):
                    return v
            except Exception:
                pass
    return {'data': getattr(resp, 'data', resp)}

def _walk_values(obj):
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_values(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk_values(v)

def _find_key(obj, names):
    for node in _walk_values(obj):
        if isinstance(node, dict):
            for n in names:
                v = node.get(n)
                if v not in (None, '') and not isinstance(v, (dict, list)):
                    return v
    return ''

def _find_image_url(obj):
    for node in _walk_values(obj):
        if isinstance(node, dict):
            for n in ('s3url', 's3_url', 'image_url', 'media_url', 'url'):
                v = node.get(n)
                if isinstance(v, str) and v.startswith('http'):
                    return v
    return ''

SOCIAL_FB_PAGE_ID = os.environ.get('SOCIAL_FB_PAGE_ID', '886504424556575')
SOCIAL_IG_USER_ID = os.environ.get('SOCIAL_IG_USER_ID', '37199314976379231')
SOCIAL_SERVICES = [
    ('House Cleaning', 'Your weekends are for LIVING, not scrubbing!', 'Cleaning', 'Bright cheerful photorealistic generic photo, sunny Central Florida home, friendly professional cleaner in turquoise polo holding a cleaning caddy, tidy living room, natural light, warm trustworthy small business, square, no text, no logo, no watermark, no before-after split, not a real customer job'),
    ('Handyman', 'That fix-it list? Consider it handled.', 'Handyman', 'Bright cheerful photorealistic generic photo, friendly handyman in turquoise polo fixing a cabinet in a sunny Central Florida home, tools nearby, warm trustworthy small business, square, no text, no logo, no watermark, no before-after split, not a real customer job'),
    ('Lawn and Yard Care', 'A yard you love, without spending your Saturday on it.', 'LawnCare', 'Bright cheerful photorealistic generic photo, friendly worker in turquoise polo trimming a green Central Florida lawn, sunny day, palm trees, warm trustworthy small business, square, no text, no logo, no watermark, no before-after split, not a real customer job'),
    ('Pressure Washing', 'Make your driveway and patio look fresh again.', 'PressureWashing', 'Bright cheerful photorealistic generic photo, friendly worker in turquoise polo pressure washing a driveway in sunny Central Florida, water spray, warm trustworthy small business, square, no text, no logo, no watermark, no before-after split, not a real customer job'),
    ('Errands and Shopping', 'Too much to do? We run it for you.', 'Errands', 'Bright cheerful photorealistic generic photo, friendly helper in turquoise polo carrying grocery bags to a sunny Central Florida home front door, warm trustworthy small business, square, no text, no logo, no watermark, not a real customer job'),
    ('Concierge and Home Tasks', 'One call. One contact. One less thing to worry about.', 'Concierge', 'Bright cheerful photorealistic generic photo, friendly concierge helper in turquoise polo holding a clipboard and house keys in a sunny Central Florida home, warm trustworthy small business, square, no text, no logo, no watermark, not a real customer job'),
    ('Home Help for Seniors and Busy Families', 'Reliable help for everyday life, for the people you love.', 'HomeHelp', 'Bright cheerful photorealistic generic photo, friendly helper in turquoise polo helping in a bright Central Florida home kitchen, kind warm trustworthy small business, square, no text, no logo, no watermark, not a real customer job'),
]

def run_social_pipeline():
    # social-auto-v1: 1 service/day by date rotation, AI image, FB+IG photo post, no human trigger needed beyond the timer calling /run-social
    try:
        now_et = datetime.datetime.now(ZoneInfo('America/New_York')) if ZoneInfo else datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
    except Exception:
        now_et = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-4)))
    svc_name, svc_hook, svc_tag, svc_prompt = SOCIAL_SERVICES[now_et.date().toordinal() % len(SOCIAL_SERVICES)]
    rep = {'date': now_et.strftime('%Y-%m-%d %H:%M ET'), 'service': svc_name, 'actions': [], 'errors': []}
    caption = ('\u2728 ' + svc_hook + ' \u2728\n' + 'Simply Just Task helps busy families, homeowners and seniors in Apopka and Central Florida with ' + svc_name.lower() + ' - reliable help for everyday life.\n' + '\U0001f4de Free consultation: (888) 566-7570\n' + '\U0001f310 simplyjusttask.com\n' + '\U0001f4c5 ' + CAL_LINK + '\n' + 'Image: AI illustration.\n' + '#Apopka #CentralFlorida #SimplyJustTask #' + svc_tag + ' #HomeTasks #Concierge')
    rep['actions'].append('service_of_day: ' + svc_name)
    image_url = ''
    image_source = ''
    try:
        g = _social_exec('GEMINI_GENERATE_IMAGE', {'prompt': svc_prompt, 'aspect_ratio': '1:1', 'image_size': '1K'})
        image_url = _find_image_url(g)
        if image_url:
            image_source = 'gemini'
        else:
            rep['errors'].append('gemini image: no url in response ' + json.dumps(g, default=str)[:300])
    except Exception as e:
        rep['errors'].append('gemini image: ' + str(e)[:200])
    if not image_url:
        import urllib.parse
        image_url = 'https://image.pollinations.ai/prompt/' + urllib.parse.quote(svc_prompt) + '?width=1024&height=1024&seed=' + str(now_et.date().toordinal()) + '&nologo=true'
        image_source = 'pollinations-fallback'
    rep['actions'].append('image_source: ' + image_source)
    rep['actions'].append('image_url_host: ' + image_url.split('/')[2] if '://' in image_url else 'image ready')
    fb_resp = _social_exec('FACEBOOK_CREATE_PHOTO_POST', {'page_id': SOCIAL_FB_PAGE_ID, 'url': image_url, 'message': caption, 'published': True})
    fb_id = _find_key(fb_resp, ('post_id', 'id'))
    if fb_id and not (isinstance(fb_resp, dict) and fb_resp.get('error')):
        rep['actions'].append('facebook_post_id: ' + str(fb_id))
    else:
        rep['errors'].append('facebook post: ' + json.dumps(fb_resp, default=str)[:500])
    ig_container = _social_exec('INSTAGRAM_POST_IG_USER_MEDIA', {'ig_user_id': SOCIAL_IG_USER_ID, 'image_url': image_url, 'caption': caption})
    ig_cid = _find_key(ig_container, ('creation_id', 'id'))
    if ig_cid and not (isinstance(ig_container, dict) and ig_container.get('error')):
        ig_pub = _social_exec('INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH', {'ig_user_id': SOCIAL_IG_USER_ID, 'creation_id': str(ig_cid), 'max_wait_seconds': 120})
        ig_mid = _find_key(ig_pub, ('id',))
        if ig_mid and not (isinstance(ig_pub, dict) and ig_pub.get('error')):
            rep['actions'].append('instagram_media_id: ' + str(ig_mid))
        else:
            rep['errors'].append('instagram publish: ' + json.dumps(ig_pub, default=str)[:500])
    else:
        rep['errors'].append('instagram container: ' + json.dumps(ig_container, default=str)[:500])
    try:
        social_tools = []
        for tk in SOCIAL_PLATFORMS:
            try:
                t = list(composio.tools.get(user_id=COMPOSIO_USER_ID, toolkits=[tk]))
                social_tools += t
            except Exception as e:
                rep['errors'].append(tk + ' reply tools: ' + str(e)[:150])
        if social_tools:
            social_agent = Agent(role='Social Media Manager', goal='Only check and warmly reply to new Simply Just Task social messages and comments, and capture buying interest as leads. Do NOT create any post today - today post was already published by social-auto-v1.', backstory='You represent Simply Just Task. Warm, human, never pushy. Booking link: ' + CAL_LINK, tools=social_tools + [save_lead], llm=llm, verbose=True)
            reply_task = Task(description='Check new unread messages/comments on Facebook and Instagram ONLY. Do NOT post. Reply warmly. If buying intent, collect name email phone service and call save_lead grade A.', expected_output='List of replies sent and leads saved, or none', agent=social_agent)
            result = Crew(agents=[social_agent], tasks=[reply_task]).kickoff()
            rep['actions'].append('reply crew: ' + str(result)[:1000])
    except Exception as e:
        rep['errors'].append('reply crew: ' + str(e)[:300])
    body = 'SOCIAL MEDIA CREW REPORT - social-auto-v1\nDate: ' + rep['date'] + '\nService: ' + svc_name + '\nCaption:\n' + caption + '\n\n' + '\n'.join(rep['actions']) + '\n\nERRORS:\n' + '\n'.join(rep['errors'])
    try:
        zoho_exec('ZOHO_MAIL_MESSAGES_SEND_EMAIL', {'accountId': ZOHO_MAIL_ACCOUNT_ID, 'fromAddress': ZOHO_FROM, 'toAddress': REPORT_EMAIL, 'ccAddress': REPORT_CC, 'subject': 'SJT Social Crew Report - ' + rep['date'], 'content': body, 'mailFormat': 'plaintext'})
    except Exception as e:
        print('social report email failed:', e)
    print(body)

'''
s = s[:start] + NEW.strip() + '\n\n' + s[end:]
debug_anchor = '"nextdoor": "kernel-personal-auth,watcher-v2,draft-only",'
assert debug_anchor in s, 'debug anchor missing'
s = s.replace(debug_anchor, debug_anchor + '\n        "social_auto": "social-auto-v1,daily-service-rotation,gemini-image,fb-ig-photo-post",', 1)
p.write_text(s)
print('patched', len(s))
