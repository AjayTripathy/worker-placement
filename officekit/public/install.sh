#!/bin/sh
set -eu
command -v git >/dev/null 2>&1 || { echo 'Install Git, then rerun this command.' >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo 'Install Python 3.9 or later, then rerun this command.' >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else "Install Python 3.9 or later, then rerun this command.")'
if [ ! -e worker-placement ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/AjayTripathy/worker-placement.git worker-placement
  git -C worker-placement sparse-checkout set officekit officekit_ai officekit_agents officekit_adapters officekit_research officekit_signals officekit_dist strategies/_template strategies/muni_dislocation
elif [ ! -f worker-placement/wp ] || [ ! -f worker-placement/start.sh ]; then
  echo 'A worker-placement folder already exists without the launcher. Update that checkout, or run from another directory.' >&2
  exit 1
fi
case "$(git -C worker-placement remote get-url origin 2>/dev/null || true)" in
  https://github.com/AjayTripathy/worker-placement.git|git@github.com:AjayTripathy/worker-placement.git) ;;
  *) echo 'The existing worker-placement folder is not the expected repository. Run from another directory.' >&2; exit 1 ;;
esac
cd worker-placement
exec ./start.sh
