from .auth_data_scanner import AuthDataScanner
from .config_scanner import ConfigScanner
from .dependency_scanner import DependencyScanner
from .deployment_scanner import DeploymentScanner
from .desktop_scanner import DesktopScanner
from .llm_agent_scanner import LlmAgentScanner
from .mcp_ipc_scanner import McpIpcScanner
from .secret_scanner import SecretScanner

DEFAULT_SCANNERS = [
    SecretScanner(),
    DependencyScanner(),
    ConfigScanner(),
    AuthDataScanner(),
    DeploymentScanner(),
    DesktopScanner(),
    McpIpcScanner(),
    LlmAgentScanner(),
]
