import subprocess, datetime, pathlib, json
start='95fb51e6c2a2dc26dd609c2b3846d65341448264'
end='db9b76ccce1242fa62fa304019c4f1c9801ccff1'
logdir=pathlib.Path('docs/patch_logs')
spec_hash=subprocess.check_output(['scripts/hash_utils.sh','cag_agents_hash','AGENTS.md']).decode().strip()
commits=subprocess.check_output(['git','rev-list','--reverse',f'{start}..{end}']).decode().split()
print('commits',len(commits))
for h in commits:
    date_iso=subprocess.check_output(['git','show','-s','--format=%cI',h]).decode().strip()
    dt=datetime.datetime.fromisoformat(date_iso.replace('Z','+00:00')).astimezone(datetime.timezone.utc)
    fname=dt.strftime('patch_%Y%m%d_%H%M%S_')+h+'.log'
    path=logdir/fname
    if path.exists():
        continue
    diff=subprocess.check_output(['git','show','--stat','--oneline',h]).decode().strip()
    body=f"""{fname}
=====TASK=====
Backfill legacy patch log

=====OBJECTIVE=====
Reconstruct patch metadata for auditing.

=====CONSTRAINTS=====
- No repository changes
- Use commit history only

=====SCOPE=====
Commit {h}

=====DIFFSUMMARY=====
{diff}

=====TIMESTAMP=====
{dt.strftime('%Y-%m-%dT%H:%M:%SZ')}

=====BUILDER_DATE_TIME (UTC)=====
20250801 200929

=====PROMPTID=====
legacy-backfill-batch-006

=====AGENTVERSION=====
LEGACY-N/A

=====AGENTHASH=====
LEGACY-N/A

=====PROMPTHASH=====
LEGACY-N/A

=====COMMITHASH=====
{h}

=====SPEC_HASHES=====
{spec_hash}

=====SNAPSHOT=====
LEGACY-N/A

=====TESTRESULTS=====
LEGACY-N/A

=====DIAGNOSTICMETA=====
{{"legacy_backfill": true}}

=====DECISIONS=====
- Legacy patch log generated from commit history.
"""
    path.write_text(body)
print('Generated',len(commits),'logs')
