# formatter.py

from __future__ import annotations
import os
import re

class TuiFormatter:
    # -----------------------------
    # Text styling
    # -----------------------------

    def supports_colour(self) -> bool:
        return True

    def colour(self, text: str, code: str) -> str:
        if not self.supports_colour():
            return text
        return f"\033[{code}m{text}\033[0m"

    def bold(self, text: str) -> str:
        return self.colour(text, "1")

    def dim(self, text: str) -> str:
        return self.colour(text, "2")

    def blue(self, text: str) -> str:
        return self.colour(text, "96")

    def green(self, text: str) -> str:
        return self.colour(text, "92")

    def red(self, text: str) -> str:
        return self.colour(text, "91")

    def print_info(self, text: str) -> None:
        print(self.blue("[info]"), text)

    def print_error(self, text: str) -> None:
        print(self.red("[error]"), text)

    def print_dim(self, text: str) -> None:
        print(self.dim(text))

    def is_code_block_start(self, line: str) -> bool:
        return line.strip().startswith("```")

    def collect_code_block(self, lines: list[str], start_index: int) -> tuple[list[str], str, int]:
        opening = lines[start_index].strip()
        language = opening[3:].strip()
        code_lines: list[str] = []
        index = start_index + 1

        while index < len(lines):
            if lines[index].strip().startswith("```"):
                return code_lines, language, index + 1

            code_lines.append(lines[index])
            index += 1

        return code_lines, language, index

    def print_tui_code_block(self, code_lines: list[str], language: str = "") -> None:
        width = self.safe_terminal_width()
        label = f" code: {language} " if language else " code "
        border_width = max(8, width - 2)

        top = "╭" + label + "─" * max(0, border_width - len(label)) + "╮"
        bottom = "╰" + "─" * border_width + "╯"

        print(self.dim(top))
        print()

        if not code_lines:
            print("")
        else:
            for code_line in code_lines:
                print(self.colour(code_line, "97"))

        print()
        print(self.dim(bottom))

    def print_tui_markdown(self, text: str) -> None:
        lines = text.strip("\n").splitlines()
        index = 0

        while index < len(lines):
            line = lines[index]

            if self.is_code_block_start(line):
                code_lines, language, index = self.collect_code_block(lines, index)
                self.print_tui_code_block(code_lines, language)
                continue

            if self.is_markdown_table_start(lines, index):
                table_lines = []
                while index < len(lines) and lines[index].strip().startswith("|"):
                    table_lines.append(lines[index])
                    index += 1
                self.print_tui_table(table_lines)
                continue

            self.print_tui_line(line)
            index += 1

    def print_tui_line(self, line: str) -> None:
        stripped = line.strip()

        if not stripped:
            print()
            return

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            title = self.normalise_terminal_keycap_numbers(title)
            title = self.apply_inline_styles(title, allow_colour=False)
            print(self.heading_colour(level, title))
            return

        if stripped in {"---", "***", "___"}:
            print(self.dim("─" * min(72, self.safe_terminal_width())))
            return

        if stripped.startswith(">"):
            quote_text = stripped.lstrip("> ").strip()
            quote_text = self.normalise_terminal_keycap_numbers(quote_text)
            print(self.colour("│ ", "90") + self.dim(self.apply_inline_styles(quote_text, allow_colour=False)))
            return

        bullet_match = re.match(r"^(\s*)([-*+] |\d+\.\s+)(.*)$", line)
        if bullet_match:
            indent, bullet, content = bullet_match.groups()
            marker = self.colour(bullet.strip(), "94")
            content = self.normalise_terminal_keycap_numbers(content)
            print(f"{indent}{marker} {self.apply_inline_styles(content)}")
            return

        print(self.apply_inline_styles(self.normalise_terminal_keycap_numbers(line)))

    def is_markdown_table_start(self, lines: list[str], index: int) -> bool:
        if index + 1 >= len(lines):
            return False

        current = lines[index].strip()
        separator = lines[index + 1].strip()

        if not current.startswith("|") or not current.endswith("|"):
            return False

        return bool(re.match(r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", separator))

    def print_tui_table(self, table_lines: list[str]) -> None:
        rows = [self.parse_table_row(line) for line in table_lines]

        if len(rows) < 2:
            for line in table_lines:
                self.print_tui_line(line)
            return

        header = rows[0]
        body = rows[2:]
        column_count = max(len(row) for row in rows if row)

        normalised_rows = [self.pad_row(header, column_count), *[self.pad_row(row, column_count) for row in body]]
        widths = self.calculate_table_column_widths(normalised_rows, column_count)

        top = "╭" + "┬".join("─" * (width + 2) for width in widths) + "╮"
        sep = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
        bottom = "╰" + "┴".join("─" * (width + 2) for width in widths) + "╯"

        print(self.dim(top))
        self.print_tui_table_row(normalised_rows[0], widths, is_header=True)
        print(self.dim(sep))
        for row in normalised_rows[1:]:
            self.print_tui_table_row(row, widths, is_header=False)
        print(self.dim(bottom))

    def calculate_table_column_widths(self, rows: list[list[str]], column_count: int) -> list[int]:
        max_width = self.safe_terminal_width()
        frame_width = 2 + column_count + 1
        padding_width = column_count * 2
        separator_width = max(0, column_count - 1)
        available_width = max_width - 2 - separator_width - padding_width

        if column_count <= 0:
            return []

        min_width = 8
        available_width = max(column_count * min_width, available_width)

        natural_widths = [0] * column_count
        for row in rows:
            for col_index, cell in enumerate(row):
                plain = self.strip_ansi(self.apply_inline_styles(self.normalise_terminal_keycap_numbers(cell)))
                longest_word = max((len(word) for word in re.findall(r"\S+", plain)), default=0)
                natural_widths[col_index] = max(natural_widths[col_index], min(max(len(plain), longest_word), 40))

        widths = [max(min_width, min(width, 40)) for width in natural_widths]

        while sum(widths) > available_width:
            widest = max(range(column_count), key=lambda index: widths[index])
            if widths[widest] <= min_width:
                break
            widths[widest] -= 1

        while sum(widths) < available_width:
            expandable = [index for index, width in enumerate(widths) if width < natural_widths[index]]
            if not expandable:
                break
            target = max(expandable, key=lambda index: natural_widths[index] - widths[index])
            widths[target] += 1

        return widths

    def parse_table_row(self, line: str) -> list[str]:
        stripped = line.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        return [cell.strip() for cell in stripped.split("|")]

    def pad_row(self, row: list[str], column_count: int) -> list[str]:
        return [*row, *([""] * (column_count - len(row)))]

    def print_tui_table_row(self, row: list[str], widths: list[int], is_header: bool) -> None:
        wrapped_cells = [self.wrap_table_cell(cell, widths[col_index]) for col_index, cell in enumerate(row)]
        row_height = max((len(lines) for lines in wrapped_cells), default=1)

        for line_index in range(row_height):
            cells = []
            for col_index, lines in enumerate(wrapped_cells):
                width = widths[col_index]
                cell_line = lines[line_index] if line_index < len(lines) else ""
                styled = self.apply_inline_styles(self.normalise_terminal_keycap_numbers(cell_line))
                styled = self.table_column_colour(col_index, styled)
                if is_header:
                    styled = self.bold(styled)
                padding = " " * max(0, width - len(self.strip_ansi(styled)))
                cells.append(f" {styled}{padding} ")
            print(self.dim("│") + self.dim("│").join(cells) + self.dim("│"))

    def wrap_table_cell(self, cell: str, width: int) -> list[str]:
        width = max(1, width)
        plain = re.sub(r"\s+", " ", cell.strip())

        if not plain:
            return [""]

        words = plain.split(" ")
        lines: list[str] = []
        current = ""

        for word in words:
            if not current:
                current = word
                continue

            candidate = f"{current} {word}"
            if len(self.strip_ansi(candidate)) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word

        if current:
            lines.append(current)

        return lines or [plain]

    def handle_resize(self) -> None:
        if getattr(self, "is_streaming_response", False):
            return

        if hasattr(self, "streaming_reply_buffer") and self.streaming_reply_buffer:
            self.flush_streaming_reply_buffer()
        self.clear_screen()
        self.show_landing_page()
        self.print_info("Connected to Ollama.")
        self.print_info(f"Model: {self.model}")
        self.print_dim("Type /help for commands. Ctrl-O collapse/expand thinking. Type /exit to quit.\n")

        if self.last_visible_reply:
            self.print_agent_header()
            self.print_model_reply(self.last_visible_reply)
            print()
            print()

    def apply_inline_styles(self, text: str, allow_colour: bool = True) -> str:
        def bold_replacer(match):
            inner = match.group(1)
            if allow_colour:
                return self.bold(self.colour(inner, "94"))
            return self.bold(inner)

        return re.sub(r"\*\*(.+?)\*\*", bold_replacer, text)

    def heading_colour(self, level: int, text: str) -> str:
        codes = {
            1: "94;1",
            2: "94",
            3: "36",
            4: "96",
            5: "90",
            6: "2",
        }
        prefix = "▌" if level <= 2 else "•"
        return self.colour(f"{prefix} {text}", codes.get(level, "90"))

    def normalise_terminal_keycap_numbers(self, text: str) -> str:
        # Some terminals render keycap number emojis like 1️⃣ as monochrome fallback
        # glyphs with dark digits, which makes them unreadable on dark backgrounds.
        # Convert only keycap-style number emojis into terminal-friendly Unicode
        # number symbols that inherit normal terminal foreground colours.
        keycap_map = {
            "10️⃣": "⑩",
            "🔟": "⑩",
            "0️⃣": "⓪",
            "1️⃣": "①",
            "2️⃣": "②",
            "3️⃣": "③",
            "4️⃣": "④",
            "5️⃣": "⑤",
            "6️⃣": "⑥",
            "7️⃣": "⑦",
            "8️⃣": "⑧",
            "9️⃣": "⑨",
        }
        for emoji, replacement in keycap_map.items():
            text = text.replace(emoji, replacement)
        return text

    def table_column_colour(self, index: int, text: str) -> str:
        pastel_codes = ["35", "36", "32", "33", "34", "31"]
        return self.colour(text, pastel_codes[index % len(pastel_codes)])

    def safe_terminal_width(self) -> int:
        try:
            return max(40, min(os.get_terminal_size().columns, 120))
        except OSError:
            return 88

    def clip_text(self, text: str, width: int) -> str:
        plain = text.strip()
        if len(plain) <= width:
            return plain
        if width <= 1:
            return plain[:width]
        return plain[: max(1, width - 1)] + "…"

    def strip_ansi(self, text: str) -> str:
        return re.sub(r"\033\[[0-9;]*m", "", text)