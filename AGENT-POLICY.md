<!-- ai-generated: 70% - drafted by Claude Code, each blast-radius decision reviewed by me -->
# Agent policy

The `reviewer` sub-agent (`.claude/agents/reviewer.md`) reads the repository and reports findings. Each entry
of its `disallowedTools` list removes an action whose blast radius goes beyond reviewing:

- Bash(rm *): the reviewer reads and comments; deleting files is the author's decision, and a deleted spec or receipted file cannot be restored from the review
- Bash(git push *): publishing to the public repository changes what the grader and the tier-a workflow see; only the author pushes, after verify passes
- Bash(git tag *): lab tags are immutable submissions and a moved or premature tag voids an attempt that still counts, so tagging stays with the author
- Bash(docker *): containers, volumes and images on the author's machine are shared state; a review has no reason to start, stop or delete them
- WebFetch: the review is judged against the files in this repository only, and fetched content could carry instructions or leak repository details
- Edit: a reviewer that edits code stops being an independent check; findings go back to the author, who decides the fix
- Write: creating or overwriting files would put unreviewed content into the tree that the next commit could pick up unnoticed
