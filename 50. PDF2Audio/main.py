"""
PDF2AUDIO - turn any PDF into an audiobook (MP3).

Free and simple: extracts the text from a PDF and converts it to speech
using Microsoft's neural voices (via the `edge-tts` package).
No account and no API key needed.

Install
-------
    python -m pip install pypdf edge-tts rich

Quick start
-----------
    python main.py book.pdf

Need help?
----------
    python main.py --help        (or -h)
"""

from __future__ import annotations

import argparse
import asyncio
import math
import re
import sys
import time
from pathlib import Path

from pypdf import PdfReader
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

console = Console()

DEFAULT_EDGE_VOICE = "en-US-AriaNeural"
DEFAULT_POLLY_VOICE = "Joanna"

BANNER = r"""
██████╗ ██████╗ ███████╗██████╗  █████╗ ██╗   ██╗██████╗ ██╗ ██████╗
██╔══██╗██╔══██╗██╔════╝╚════██╗██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗
██████╔╝██║  ██║█████╗   █████╔╝███████║██║   ██║██║  ██║██║██║   ██║
██╔═══╝ ██║  ██║██╔══╝  ██╔═══╝ ██╔══██║██║   ██║██║  ██║██║██║   ██║
██║     ██████╔╝██║     ███████╗██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝
╚═╝     ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝
"""


# --------------------------------------------------------------------------- #
#  UI helpers
# --------------------------------------------------------------------------- #
def gradient_text(block: str, start=(0, 224, 255), end=(255, 70, 200)) -> Text:
    """Color a block of text with a left-to-right RGB gradient."""
    lines = block.strip("\n").splitlines()
    width = max(len(line) for line in lines)
    text = Text()
    for line in lines:
        for i, ch in enumerate(line):
            t = i / max(width - 1, 1)
            r, g, b = (int(s + (e - s) * t) for s, e in zip(start, end))
            text.append(ch, style=f"bold #{r:02x}{g:02x}{b:02x}")
        text.append("\n")
    text.rstrip()
    return text


def make_wave(width: int) -> str:
    """A little audio-waveform made of block characters."""
    bars = "▁▂▃▄▅▆▇█"
    out = []
    for i in range(width):
        v = (math.sin(i / 2.3) + math.sin(i / 5.1) * 0.8 + 1.8) / 3.6
        out.append(bars[min(int(v * len(bars)), len(bars) - 1)])
    return "".join(out)


def show_banner() -> None:
    art_width = max(len(line) for line in BANNER.strip("\n").splitlines())

    art = gradient_text(BANNER)
    wave = gradient_text(make_wave(art_width), start=(255, 70, 200), end=(0, 224, 255))
    tagline = Text("Too tired to read? Let your PDF read itself to you.",
                   style="italic bright_white")
    sub = Text("PDF  →  neural text-to-speech  →  MP3", style="dim cyan")

    console.print()
    console.print(
        Panel(
            Align.center(
                Group(
                    Align.center(art),
                    Text(""),
                    Align.center(wave),
                    Text(""),
                    Align.center(tagline),
                    Align.center(sub),
                )
            ),
            border_style="bright_magenta",
            box=box.DOUBLE,
            padding=(1, 2),
        )
    )


def make_progress() -> Progress:
    return Progress(
        SpinnerColumn("dots12", style="cyan"),
        TextColumn("[bold]{task.description}"),
        BarColumn(bar_width=None, complete_style="magenta", finished_style="green"),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


# --------------------------------------------------------------------------- #
#  PDF -> text
# --------------------------------------------------------------------------- #
def parse_page_ranges(spec: str | None, total: int) -> list[int]:
    """'1-3,7' -> [0, 1, 2, 6] (zero-based indices)."""
    if not spec:
        return list(range(total))
    pages: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else total
        else:
            start = end = int(part)
        if start < 1 or end > total or start > end:
            raise ValueError(f"Page range '{part}' is outside 1-{total}")
        pages.extend(range(start - 1, end))
    return pages


def clean_text(raw: str) -> str:
    """Tidy up text that was extracted from a PDF so it reads naturally."""
    text = raw.replace("\u00ad", "")                 # soft hyphens
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)     # re-join hyphenated words
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)           # keep paragraph breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)     # single newline -> space
    return text.strip()


def extract_text(pdf_path: Path, page_spec: str | None) -> str:
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:  # corrupt / not a PDF
        console.print(f"[bold red]Could not open PDF:[/] {exc}")
        sys.exit(1)

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            console.print("[bold red]This PDF is password protected.[/]")
            sys.exit(1)

    try:
        indices = parse_page_ranges(page_spec, len(reader.pages))
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/]")
        sys.exit(1)

    pieces: list[str] = []
    with make_progress() as progress:
        task = progress.add_task("Reading pages", total=len(indices))
        for i in indices:
            pieces.append(reader.pages[i].extract_text() or "")
            progress.advance(task)

    text = clean_text("\n\n".join(pieces))
    if not text:
        console.print(
            Panel(
                "No text found. This looks like a scanned PDF (images only).\n"
                "Run OCR on it first, for example with [bold]ocrmypdf[/].",
                title="Nothing to read",
                border_style="red",
            )
        )
        sys.exit(1)
    return text


def chunk_text(text: str, max_chars: int) -> list[str]:
    """Split on sentence boundaries so no chunk exceeds max_chars."""
    sentences = re.split(r"(?<=[.!?])\s+|\n\n", text)
    chunks: list[str] = []
    current = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # A single monster sentence: hard-split on whitespace.
        while len(s) > max_chars:
            cut = s.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if current:
                chunks.append(current)
                current = ""
            chunks.append(s[:cut])
            s = s[cut:].strip()
        if len(current) + len(s) + 1 > max_chars:
            chunks.append(current)
            current = s
        else:
            current = f"{current} {s}".strip()
    if current:
        chunks.append(current)
    return chunks


# --------------------------------------------------------------------------- #
#  TTS engines
# --------------------------------------------------------------------------- #
async def edge_synthesize(text: str, voice: str, rate: str, retries: int = 3) -> bytes:
    import edge_tts

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            audio = bytearray()
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            async for msg in communicate.stream():
                if msg["type"] == "audio":
                    audio.extend(msg["data"])
            if not audio:
                raise RuntimeError("Service returned no audio")
            return bytes(audio)
        except Exception as exc:
            last_exc = exc
            await asyncio.sleep(1.5 * attempt)
    raise RuntimeError(f"edge-tts failed after {retries} attempts: {last_exc}")


def polly_client():
    try:
        import boto3
    except ImportError:
        console.print("[bold red]boto3 is not installed.[/] Run: python -m pip install boto3")
        sys.exit(1)
    return boto3.client("polly")


def polly_synthesize(client, text: str, voice: str) -> bytes:
    resp = client.synthesize_speech(
        Text=text, OutputFormat="mp3", VoiceId=voice, Engine="neural"
    )
    return resp["AudioStream"].read()


async def list_edge_voices(lang: str | None) -> None:
    import edge_tts

    voices = await edge_tts.list_voices()
    if lang:
        voices = [v for v in voices if v["Locale"].lower().startswith(lang.lower())]
    table = Table(title="Available voices (edge)", box=box.ROUNDED,
                  header_style="bold magenta", border_style="bright_blue")
    table.add_column("Voice", style="cyan")
    table.add_column("Gender")
    table.add_column("Locale", style="green")
    for v in sorted(voices, key=lambda v: (v["Locale"], v["ShortName"])):
        table.add_row(v["ShortName"], v["Gender"], v["Locale"])
    console.print(table)


# --------------------------------------------------------------------------- #
#  Main pipeline
# --------------------------------------------------------------------------- #
async def convert(args: argparse.Namespace) -> None:
    pdf_path = Path(args.pdf).expanduser()
    if not pdf_path.is_file():
        console.print(f"[bold red]File not found:[/] {pdf_path}")
        sys.exit(1)

    out_path = Path(args.output) if args.output else pdf_path.with_suffix(".mp3")
    voice = args.voice or (DEFAULT_POLLY_VOICE if args.engine == "polly" else DEFAULT_EDGE_VOICE)
    max_chars = 2500 if args.engine == "polly" else 3000

    # 1) Extract
    text = extract_text(pdf_path, args.pages)
    chunks = chunk_text(text, max_chars)
    words = len(text.split())
    est_minutes = words / 150  # ~150 wpm narration

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan")
    info.add_column()
    info.add_row("Source", str(pdf_path))
    info.add_row("Output", str(out_path))
    info.add_row("Engine", args.engine)
    info.add_row("Voice", voice)
    info.add_row("Words", f"{words:,}  ({len(text):,} characters)")
    info.add_row("Chunks", str(len(chunks)))
    info.add_row("Est. length", f"~{est_minutes:.0f} min of audio")
    console.print(Panel(info, title="Job summary", border_style="magenta", box=box.ROUNDED))

    if args.dry_run:
        console.print("[yellow]Dry run: nothing was synthesized.[/]")
        return

    client = polly_client() if args.engine == "polly" else None

    # 2) Synthesize
    start = time.time()
    try:
        with open(out_path, "wb") as f, make_progress() as progress:
            task = progress.add_task("Speaking", total=len(chunks))
            for chunk in chunks:
                if args.engine == "polly":
                    data = await asyncio.to_thread(polly_synthesize, client, chunk, voice)
                else:
                    data = await edge_synthesize(chunk, voice, args.rate)
                f.write(data)  # MP3 frames can simply be concatenated
                progress.advance(task)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled. Partial file kept.[/]")
        return
    except Exception as exc:
        console.print(f"\n[bold red]Synthesis failed:[/] {exc}")
        sys.exit(1)

    size_mb = out_path.stat().st_size / 1_048_576
    console.print(
        Panel(
            Text.from_markup(
                f"[bold green]Done![/] Your audiobook is ready.\n\n"
                f"[cyan]{out_path}[/]  ({size_mb:.1f} MB, built in {time.time() - start:.0f}s)\n"
                f"Put on your headphones and close your eyes."
            ),
            border_style="green",
            box=box.DOUBLE,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert a PDF into an MP3 audiobook using a text-to-speech API.",
    )
    p.add_argument("pdf", nargs="?", help="Path to the PDF file")
    p.add_argument("-o", "--output", help="Output MP3 path (default: same name as PDF)")
    p.add_argument("-e", "--engine", choices=["edge", "polly"], default="edge",
                   help="TTS engine (default: edge)")
    p.add_argument("-v", "--voice", help="Voice name (engine specific)")
    p.add_argument("-r", "--rate", default="+0%",
                   help="Speaking speed for edge, e.g. +15%% or --rate=-10%% (default: +0%%)")
    p.add_argument("-p", "--pages", help="Pages to read, e.g. 1-5,9 (default: all)")
    p.add_argument("--list-voices", action="store_true", help="List edge voices and exit")
    p.add_argument("--lang", help="Filter --list-voices by locale prefix, e.g. en or ar")
    p.add_argument("--dry-run", action="store_true",
                   help="Extract text and show stats without calling the TTS API")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()  # --help is handled here by argparse and exits
    show_banner()

    if args.list_voices:
        asyncio.run(list_edge_voices(args.lang))
        return

    if not args.pdf:
        parser.print_help()  # no file given -> show the standard help screen
        return

    asyncio.run(convert(args))


if __name__ == "__main__":
    main()