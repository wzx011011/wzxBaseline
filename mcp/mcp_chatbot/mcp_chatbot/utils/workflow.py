"""The workflow tracer for the chatbot.

Example:
-------
WorkflowTrace
├── 🔍 USER_QUERY: Please summarize the content of the ...
├── 💭 LLM_THINKING: LLM is processing your query...
├── 🤖 LLM_RESPONSE: { "tool": "read_markdown_file", "arguments
├── 🔧 TOOL_CALL: Call 1: read_markdown_file
│   └── Tool: read_markdown_file, Args: {"directory_path": "...
├── ⚡️ TOOL_EXECUTION: Executing read_markdown_file...
├── 📊 TOOL_RESULT: Success
│   └── Status: Success
│      └── Result: meta=None content=[TextContent(type='text', tex...
├── 💭 LLM_THINKING: LLM processing tool results (iteration 1)...
├── 🤖 LLM_RESPONSE: { "tool": "write_markdown_file", "argument
├── 🔧 TOOL_CALL: Call 1: write_markdown_file
│   └── Tool: write_markdown_file, Args: {"directory_path": "...
├── ⚡️ TOOL_EXECUTION: Executing write_markdown_file...
├── 📊 TOOL_RESULT: Success
│   └── Status: Success
│      └── Result: meta=None content=[TextContent(type='text', tex...
├── 💭 LLM_THINKING: LLM processing tool results (iteration 2)...
├── 🤖 LLM_RESPONSE: 看起来在指定的目录下已经存在名为`summary.md`的文件，...
└── ✅ FINAL_RESPONSE: Final response after 2 tool iterations
"""

import json
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import colorama


class WorkflowEventType(Enum):
    USER_QUERY = "USER_QUERY"
    LLM_THINKING = "LLM_THINKING"
    LLM_RESPONSE = "LLM_RESPONSE"
    TOOL_CALL = "TOOL_CALL"
    TOOL_EXECUTION = "TOOL_EXECUTION"
    TOOL_RESULT = "TOOL_RESULT"
    FINAL_RESPONSE = "FINAL_RESPONSE"
    CONTEXT_OPTIMIZATION = "CONTEXT_OPTIMIZATION"


class WorkflowEvent:
    def __init__(
        self,
        event_type: WorkflowEventType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ):
        self.event_type = event_type
        self.message = message
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
        self.formatted_time = datetime.fromtimestamp(self.timestamp).strftime(
            "%H:%M:%S.%f"
        )[:-3]


class WorkflowTracer:
    def __init__(self):
        self.events: List[WorkflowEvent] = []

    def add_event(
        self,
        event_type: WorkflowEventType,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        event = WorkflowEvent(event_type, message, metadata)
        self.events.append(event)
        return event

    def _format_json_content(self, content: str, max_length: int = 70) -> str:
        """Format JSON content by compressing it into a single line.

        Args:
            content: The content to format
            max_length: Maximum length before truncation

        Returns:
            Formatted string
        """
        # Try to parse as JSON and compress
        try:
            if "{" in content and ('"tool"' in content or '"arguments"' in content):
                # Remove newlines and extra spaces
                compressed = content.replace("\n", " ").strip()
                # Replace multiple spaces with a single space
                while "  " in compressed:
                    compressed = compressed.replace("  ", " ")
                # Truncate if too long
                if len(compressed) > max_length:
                    return compressed[: max_length - 3] + "..."
                return compressed
        except Exception:
            pass

        # If not JSON or couldn't compress, just truncate if needed
        if len(content) > max_length:
            return content[: max_length - 3] + "..."
        return content

    def render_tree_workflow(self) -> str:
        """Render workflow trace as a tree-like structure.

        Returns:
            A formatted tree string representing the workflow
        """
        if not self.events:
            return "No workflow events recorded"

        # Color definitions
        COLORS = {
            WorkflowEventType.USER_QUERY: colorama.Fore.GREEN,
            WorkflowEventType.LLM_THINKING: colorama.Fore.BLUE,
            WorkflowEventType.LLM_RESPONSE: colorama.Fore.YELLOW,
            WorkflowEventType.TOOL_CALL: colorama.Fore.CYAN,
            WorkflowEventType.TOOL_EXECUTION: colorama.Fore.MAGENTA,
            WorkflowEventType.TOOL_RESULT: colorama.Fore.BLUE,
            WorkflowEventType.FINAL_RESPONSE: colorama.Fore.WHITE,
            WorkflowEventType.CONTEXT_OPTIMIZATION: colorama.Fore.GREEN,
        }

        # Icons
        ICONS = {
            WorkflowEventType.USER_QUERY: "🔍",
            WorkflowEventType.LLM_THINKING: "💭",
            WorkflowEventType.LLM_RESPONSE: "🤖",
            WorkflowEventType.TOOL_CALL: "🔧",
            WorkflowEventType.TOOL_EXECUTION: "⚡️",
            WorkflowEventType.TOOL_RESULT: "📊",
            WorkflowEventType.FINAL_RESPONSE: "✅",
            WorkflowEventType.CONTEXT_OPTIMIZATION: "📦",
        }

        output = []
        title = (
            f"{colorama.Style.BRIGHT}{colorama.Fore.CYAN}"
            f"WorkflowTrace{colorama.Style.RESET_ALL}"
        )
        output.append(title)

        for i, event in enumerate(self.events):
            color = COLORS.get(event.event_type, colorama.Fore.WHITE)
            icon = ICONS.get(event.event_type, "•")

            # Format message, handling JSON specially
            message = event.message
            if event.event_type == WorkflowEventType.LLM_RESPONSE:
                message = self._format_json_content(message)

            # Tree structure - last item gets └── others get ├──
            is_last = i == len(self.events) - 1
            prefix = "└── " if is_last else "├── "

            # Main event line with BOLD event type
            event_type_str = (
                f"{colorama.Style.BRIGHT}{event.event_type.name}{colorama.Style.NORMAL}"
            )

            line = (
                f"{colorama.Fore.CYAN}{prefix}{color}{icon} "
                f"{event_type_str}: {colorama.Style.RESET_ALL}{message}"
            )
            output.append(line)

            # Add metadata details with appropriate indentation
            detail_prefix = "    " if is_last else "│   "

            if (
                event.event_type == WorkflowEventType.TOOL_CALL
                and "tool_name" in event.metadata
            ):
                tool_name = event.metadata.get("tool_name", "unknown")
                if "arguments" in event.metadata:
                    args = json.dumps(event.metadata["arguments"])
                    if len(args) > 50:
                        args = args[:47] + "..."
                    output.append(
                        f"{colorama.Fore.CYAN}{detail_prefix}"
                        f"└── Tool: {colorama.Fore.WHITE}{tool_name}"
                        f"{colorama.Fore.CYAN}, Args: {colorama.Fore.WHITE}{args}"
                        f"{colorama.Style.RESET_ALL}"
                    )
                else:
                    output.append(
                        f"{colorama.Fore.CYAN}{detail_prefix}"
                        f"└── Tool: {colorama.Fore.WHITE}{tool_name}"
                        f"{colorama.Style.RESET_ALL}"
                    )

            elif (
                event.event_type == WorkflowEventType.TOOL_RESULT
                and "success" in event.metadata
            ):
                success = event.metadata.get("success", False)
                status_color = colorama.Fore.GREEN if success else colorama.Fore.RED
                status_text = "Success" if success else "Failed"
                output.append(
                    f"{colorama.Fore.CYAN}{detail_prefix}"
                    f"└── Status: {status_color}{status_text}"
                    f"{colorama.Style.RESET_ALL}"
                )

                # Add abbreviated result if available and successful
                if success and "result" in event.metadata and event.metadata["result"]:
                    result = str(event.metadata["result"])
                    if len(result) > 50:
                        result = result[:47] + "..."
                    output.append(
                        f"{colorama.Fore.CYAN}{detail_prefix}"
                        f"   └── Result: {colorama.Fore.WHITE}{result}"
                        f"{colorama.Style.RESET_ALL}"
                    )

        return "\n".join(output)
