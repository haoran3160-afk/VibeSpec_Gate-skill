from .gitleaks_adapter import GitleaksAdapter
from .semgrep_adapter import SemgrepAdapter
from .trivy_adapter import TrivyAdapter
from .zap_adapter import ZapAdapter

DEFAULT_ADAPTERS = [GitleaksAdapter(), TrivyAdapter(), SemgrepAdapter(), ZapAdapter()]
