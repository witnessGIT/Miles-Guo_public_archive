#!/usr/bin/env python3
"""Read public GETTR JSON for already-owned C2 evidence; never fetch media."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
import c2_metadata_evidence as cm

MAX_BYTES = 262144
POST_PATH = re.compile(r'/post/([a-z0-9]{5,40})\Z')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('GETTR metadata redirects are not allowed')


def post_id_from_url(url):
    p = urlsplit(url)
    found = POST_PATH.fullmatch(p.path)
    if p.scheme != 'https' or p.hostname not in {'gettr.com', 'www.gettr.com'} or p.port is not None or p.username is not None or p.password is not None or p.query or p.fragment or not found:
        raise ValueError('Expected exact HTTPS GETTR post target already in source evidence')
    return found.group(1)


def summarize_json(raw, expected_id):
    payload = json.loads(raw.decode('utf-8'))
    data = payload.get('result', {}).get('data')
    if not isinstance(data, dict) or data.get('_id') != expected_id:
        raise ValueError('API object does not identify the exact requested post')
    return {
        'post_id': data['_id'], 'object_type': data.get('_t'),
        'p_type': data.get('p_type'), 'uploader_id': data.get('uid'),
        'created_at_epoch_ms': data.get('cdate'), 'updated_at_epoch_ms': data.get('udate'),
        'duration_sec_as_reported': data.get('vid_dur'),
        'has_vid_field': bool(data.get('vid')), 'has_original_video_field': bool(data.get('ovid')),
        'has_external_embed_field': bool(data.get('prevsrc')),
        'reposted_ids': data.get('rpstIds'),
        'text_prefix': str(data.get('txt') or '')[:200],
        'warning': 'These are platform object fields, not proof that uploaded footage was never livestreamed. Missing p_type is unknown; no automatic review decision.'
    }


def process_request(path):
    request = cm.read_json(path)
    if request.get('request_version') != 'c2-platform-request-v1':
        raise ValueError('Invalid request version')
    tasks = request.get('task_ids')
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 20 or len(set(tasks)) != len(tasks):
        raise ValueError('Expected 1..20 unique owned task IDs')
    revision = str(request.get('page_evidence_revision') or '')
    if not re.fullmatch(r'[0-9a-f]{16}', revision):
        raise ValueError('Invalid source-evidence revision')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    for task in tasks:
        if not isinstance(task, str) or not cm.SAFE_ID.fullmatch(task) or not task.startswith('C2-REVIEW-'):
            raise ValueError('Invalid task ID')
        out = cm.ROOT / 'data/source_page_evidence/c2_platform' / task / (digest[:16] + '.json')
        if out.exists() or (cm.ROOT / 'coordination/completed' / (task+'.json')).exists():
            continue
        claim, candidate, gwins_url = cm.validate_member(task, request['agent_id'], request['review_batch_id'])
        ep = cm.ROOT / 'data/source_page_evidence/c2_metadata' / task / (revision+'.json')
        evidence = cm.read_json(ep)
        if evidence.get('task_id') != task or evidence.get('source_candidate_id') != candidate['id'] or evidence.get('status') != 'fetched' or evidence.get('requested_url') != gwins_url:
            raise ValueError('Source-page evidence does not match the exact owned candidate')
        targets = []
        for url in evidence.get('metadata_evidence', {}).get('outbound_links', []):
            try:
                pid = post_id_from_url(url)
            except (ValueError, TypeError):
                continue
            targets.append((url, pid))
        if len(targets) != 1:
            raise ValueError('Requires exactly one observed GETTR post target')
        url, pid = targets[0]
        api_url = 'https://api.gettr.com/u/post/' + pid
        result = {'evidence_version':'c2-platform-evidence-v1', 'task_id':task,
                  'source_candidate_id':candidate['id'], 'agent_id':claim['agent_id'],
                  'request_sha256':digest, 'source_evidence_path':str(ep.relative_to(cm.ROOT)),
                  'public_post_url':url, 'api_url':api_url, 'fetched_at':cm.now(),
                  'review_decision':None, 'media_download_performed':False}
        try:
            req = Request(api_url, headers={'User-Agent':'Miles-Guo_public_archive/metadata-evidence-v1','Accept':'application/json'})
            with build_opener(NoRedirect()).open(req, timeout=20) as response:
                if response.headers.get_content_type() != 'application/json':
                    raise ValueError('Non-JSON response refused')
                raw = response.read(MAX_BYTES+1)
                if len(raw) > MAX_BYTES:
                    raise ValueError('Metadata exceeds size limit')
                result.update({'status':'fetched','http_status':response.status,
                               'raw_sha256':hashlib.sha256(raw).hexdigest(), 'raw_bytes':len(raw),
                               'platform_metadata':summarize_json(raw,pid)})
        except Exception as exc:
            result.update({'status':'fetch_failed','error':f'{type(exc).__name__}: {exc}'[:500]})
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open('x', encoding='utf-8') as fh:
            json.dump(result,fh,ensure_ascii=False,indent=2); fh.write('\n')
        print(json.dumps({'task_id':task,'status':result['status'],'output':str(out.relative_to(cm.ROOT))}))
        time.sleep(1)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request',type=Path,required=True)
    process_request(p.parse_args().request)
