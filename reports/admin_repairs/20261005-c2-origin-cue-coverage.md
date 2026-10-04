# C2 metadata origin-cue coverage

Agent: `agent-20261004T125231Z-chat-c2-gw3`. Authenticated GitHub login reverified as `witnessGIT`; admin maintenance under the existing AGENT_PERMISSIONS policy.

Continuation of the fixed 20-member ordinary-chat batch. No new candidate claim, completion, canonical promotion or scope change is made by this repair.

The original parser did not return colloquial video/recording or duration references such as 小视频, 拍一段, 視頻 or 10分钟 unless another narrow recording/live regex happened to match. This could hide potentially relevant origin context. Expanded the cue search and recorded `cue_profile=origin-context-v2`. Every excerpt still requires candidate-specific human/contextual assessment. Mentioning another video, a future livestream, or a number of minutes is not an automatic type decision.

The base module was reconstructed offline from the fetched current file and matched Git blob `135803051acdf3fea08c1e69551369c8e9b9b21e` exactly. Five new focused tests ran before the change: they failed with seven failing assertions across subtests. The same five tests passed after the change. Existing full-repository checks are left to CI; no local clone or database build is claimed.

The change preserves URL/redirect allowlists, active owned-claim checks, response bounds, 40-cue limit, hidden-text exclusion, damaged-excerpt exclusion, no-media behavior, no automatic decisions, and immutable request-hash receipts. The revision-3 request contains only the nine unfinished members already owned by this batch. Prior receipts are retained.
