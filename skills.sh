#!/bin/bash
# skills.sh — thin wrapper around npx skills CLI
# Full registry: https://skills.sh
# Usage:
#   ./skills.sh bootstrap          install core cxostack skills
#   ./skills.sh install <owner/repo@skill> [user|project]
#   ./skills.sh list
#   ./skills.sh find <query>       delegates to npx skills find

case "$1" in

  bootstrap)
    echo "Installing core cxostack skills..."

    # TL meta-skills (must come first — TL uses these to find everything else)
    npx skills add vercel-labs/skills --skill find-skills        -a claude-code -g -y

    # CXOtack operation skills
    npx skills add obra/superpowers --skill subagent-driven-development  -a claude-code -g -y
    npx skills add obra/superpowers --skill dispatching-parallel-agents  -a claude-code -g -y
    npx skills add obra/superpowers --skill using-git-worktrees          -a claude-code -g -y
    npx skills add obra/superpowers --skill finishing-a-development-branch -a claude-code -g -y
    npx skills add obra/superpowers --skill requesting-code-review       -a claude-code -g -y
    npx skills add obra/superpowers --skill verification-before-completion -a claude-code -g -y

    # Frontend developer
    npx skills add anthropics/skills          --skill frontend-design             -a claude-code -g -y
    npx skills add nextlevelbuilder/ui-ux-pro-max-skill --skill ui-ux-pro-max     -a claude-code -g -y
    npx skills add vercel-labs/agent-skills   --skill vercel-react-best-practices -a claude-code -g -y

    # Backend developer
    npx skills add supabase/agent-skills      --skill supabase-postgres-best-practices -a claude-code -g -y
    npx skills add wshobson/agents            --skill nodejs-backend-patterns           -a claude-code -g -y
    npx skills add better-auth/skills         --skill better-auth-best-practices        -a claude-code -g -y

    # QA
    npx skills add anthropics/skills          --skill webapp-testing         -a claude-code -g -y
    npx skills add wshobson/agents            --skill e2e-testing-patterns   -a claude-code -g -y

    # Code reviewer
    npx skills add wshobson/agents            --skill code-review-excellence -a claude-code -g -y

    echo ""
    echo "✓ Bootstrap complete. Run ./skills.sh list to verify."
    ;;

  install)
    SKILL_REF="$2"      # e.g. vercel-labs/agent-skills@vercel-react-best-practices
    SCOPE="${3:-user}"

    [ -z "$SKILL_REF" ] && echo "Usage: ./skills.sh install <owner/repo@skill> [user|project]" && exit 1

    FLAGS="-a claude-code -y"
    [ "$SCOPE" = "user" ] && FLAGS="$FLAGS -g"

    npx skills add "$SKILL_REF" $FLAGS
    ;;

  find)
    # delegates entirely to npx skills — TL can also call this directly
    npx skills find "$2"
    ;;

  list)
    npx skills list 2>/dev/null || ls ~/.claude/skills/
    ;;

  *)
    echo "Usage:"
    echo "  ./skills.sh bootstrap                      install all core cxostack skills"
    echo "  ./skills.sh install <owner/repo@skill>     install a specific skill"
    echo "  ./skills.sh find <query>                   search skills.sh registry"
    echo "  ./skills.sh list                           show installed skills"
    ;;
esac
