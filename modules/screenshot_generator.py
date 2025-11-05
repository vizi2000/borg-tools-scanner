"""
Screenshot Generator Module for Borg Tools Scanner

Implements 4 strategies for generating project screenshots:
1. Extract from README (fast ~100ms)
2. Capture real screenshots via Playwright (slow ~30-60s)
3. AI-generated HTML mockup with Minimax M2 (medium ~10-20s)
4. SVG placeholder fallback (fast ~50ms)

Created by The Collective Borg.tools
"""

import asyncio
import base64
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from urllib.parse import urljoin, urlparse

try:
    import httpx
except ImportError:
    httpx = None

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    async_playwright = None
    PlaywrightTimeout = Exception


class ScreenshotGenerator:
    """Main screenshot generator class with multiple strategies"""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.screenshots_dir = self.project_path / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

    async def generate(
        self,
        strategy: str = "auto",
        max_screenshots: int = 4,
        openrouter_api_key: Optional[str] = None
    ) -> List[str]:
        """
        Generate screenshots using specified strategy

        Args:
            strategy: auto, extract, real, mock, placeholder
            max_screenshots: Maximum number of screenshots to generate
            openrouter_api_key: API key for Minimax M2 (for mock strategy)

        Returns:
            List of screenshot file paths
        """
        screenshots = []

        if strategy == "auto":
            # Try strategies in priority order
            screenshots = await self._extract_readme_images(max_screenshots)

            if not screenshots and openrouter_api_key:
                screenshots = await self._generate_html_mockup(openrouter_api_key, max_screenshots)

            if not screenshots:
                screenshots = await self._capture_real_screenshots(max_screenshots)

            # Always fallback to placeholder if nothing worked
            if not screenshots:
                screenshots = [await self._generate_svg_placeholder()]

        elif strategy == "extract":
            screenshots = await self._extract_readme_images(max_screenshots)

        elif strategy == "real":
            screenshots = await self._capture_real_screenshots(max_screenshots)

        elif strategy == "mock":
            if not openrouter_api_key:
                print("Warning: mock strategy requires openrouter_api_key, falling back to placeholder")
                screenshots = [await self._generate_svg_placeholder()]
            else:
                screenshots = await self._generate_html_mockup(openrouter_api_key, max_screenshots)

        elif strategy == "placeholder":
            screenshots = [await self._generate_svg_placeholder()]

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        # Ensure at least one image (placeholder)
        if not screenshots:
            screenshots = [await self._generate_svg_placeholder()]

        return screenshots

    # Strategy 1: Extract from README
    async def _extract_readme_images(self, max_images: int = 4) -> List[str]:
        """Extract images from README.md"""
        readme_path = self._find_readme()
        if not readme_path:
            return []

        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"Error reading README: {e}")
            return []

        images = []

        # Match markdown images: ![alt](url)
        md_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        for match in re.finditer(md_pattern, content):
            url = match.group(2)
            images.append(url)

        # Match HTML images: <img src="url">
        html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
        for match in re.finditer(html_pattern, content, re.IGNORECASE):
            url = match.group(1)
            images.append(url)

        # Process and download images
        downloaded = []
        for i, url in enumerate(images[:max_images]):
            try:
                if url.startswith('http://') or url.startswith('https://'):
                    # Download remote image
                    local_path = await self._download_image(url, i)
                    if local_path:
                        downloaded.append(local_path)
                else:
                    # Local file path
                    local_path = self.project_path / url
                    if local_path.exists():
                        # Copy to screenshots directory
                        dest = self.screenshots_dir / f"readme_{i}{local_path.suffix}"
                        import shutil
                        shutil.copy(local_path, dest)
                        downloaded.append(str(dest))
            except Exception as e:
                print(f"Error processing image {url}: {e}")
                continue

        return downloaded

    async def _download_image(self, url: str, index: int) -> Optional[str]:
        """Download image from URL"""
        if not httpx:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Determine file extension from content-type or URL
                content_type = response.headers.get('content-type', '')
                ext = '.png'
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'svg' in content_type:
                    ext = '.svg'

                dest = self.screenshots_dir / f"readme_{index}{ext}"
                dest.write_bytes(response.content)
                return str(dest)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    # Strategy 2: Capture Real Screenshots
    async def _capture_real_screenshots(self, max_screenshots: int = 4) -> List[str]:
        """Capture screenshots from running web application"""
        if not async_playwright:
            print("Playwright not installed, skipping real screenshot capture")
            return []

        # Detect start command and port
        start_cmd, port = self._detect_start_command()
        if not start_cmd:
            print("Could not detect start command for web app")
            return []

        # Start server
        process = await self._start_server(start_cmd)
        if not process:
            return []

        screenshots = []
        try:
            # Wait for server to be ready
            if not await self._wait_for_port(port, timeout=60):
                print(f"Server did not start on port {port} within timeout")
                return []

            # Detect routes
            routes = self._detect_routes()
            urls = [f"http://localhost:{port}{route}" for route in routes[:max_screenshots]]

            # Capture screenshots with Playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={'width': 1280, 'height': 800})

                for i, url in enumerate(urls):
                    try:
                        await page.goto(url, timeout=10000, wait_until='networkidle')
                        screenshot_path = self.screenshots_dir / f"screenshot_{i}.png"
                        await page.screenshot(path=str(screenshot_path), full_page=False)
                        screenshots.append(str(screenshot_path))
                    except Exception as e:
                        print(f"Error capturing {url}: {e}")
                        continue

                await browser.close()

        finally:
            # Kill server
            self._kill_server(process)

        return screenshots

    def _detect_start_command(self) -> Tuple[Optional[str], int]:
        """Detect start command and port for web application"""
        # Check package.json for Node.js apps
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding='utf-8'))
                scripts = data.get('scripts', {})

                if 'dev' in scripts:
                    return ('npm run dev', self._extract_port(scripts['dev']))
                elif 'start' in scripts:
                    return ('npm start', self._extract_port(scripts['start']))
            except Exception:
                pass

        # Check for Python web frameworks
        if (self.project_path / "manage.py").exists():
            return ('python manage.py runserver', 8000)

        if (self.project_path / "app.py").exists() or (self.project_path / "main.py").exists():
            return ('python app.py', 5000)  # Flask default

        # Check for Rust/Cargo
        if (self.project_path / "Cargo.toml").exists():
            return ('cargo run', 8080)

        return (None, 3000)

    def _extract_port(self, command: str) -> int:
        """Extract port number from command string"""
        port_match = re.search(r'(?:port[=:\s]+|:)(\d{4,5})', command, re.IGNORECASE)
        if port_match:
            return int(port_match.group(1))
        return 3000  # default

    async def _start_server(self, command: str) -> Optional[subprocess.Popen]:
        """Start dev server in background"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(self.project_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            await asyncio.sleep(2)  # Give it time to start
            return process
        except Exception as e:
            print(f"Error starting server: {e}")
            return None

    def _kill_server(self, process: subprocess.Popen):
        """Kill server process"""
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    async def _wait_for_port(self, port: int, timeout: int = 60) -> bool:
        """Wait for port to become available"""
        if not httpx:
            await asyncio.sleep(5)  # Fallback wait
            return True

        start = time.time()
        while time.time() - start < timeout:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    await client.get(f"http://localhost:{port}")
                    return True
            except Exception:
                await asyncio.sleep(1)

        return False

    def _detect_routes(self) -> List[str]:
        """Detect routes from codebase"""
        routes = ['/']  # Always include homepage

        # Search for React Router routes
        for file_path in self.project_path.rglob('*.jsx'):
            if self._should_skip_file(file_path):
                continue
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Match: <Route path="/about" ...>
                for match in re.finditer(r'<Route\s+path=["\']([^"\']+)["\']', content):
                    route = match.group(1)
                    if ':' not in route and route not in routes:  # Skip param routes
                        routes.append(route)
            except Exception:
                continue

        # Search for Express routes (Node.js)
        for file_path in self.project_path.rglob('*.js'):
            if self._should_skip_file(file_path):
                continue
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Match: app.get('/api/users', ...)
                for match in re.finditer(r'app\.(get|post|put|delete)\(["\']([^"\']+)["\']', content):
                    route = match.group(2)
                    if ':' not in route and route not in routes:
                        routes.append(route)
            except Exception:
                continue

        # Search for Flask routes (Python)
        for file_path in self.project_path.rglob('*.py'):
            if self._should_skip_file(file_path):
                continue
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                # Match: @app.route('/about')
                for match in re.finditer(r'@app\.route\(["\']([^"\']+)["\']', content):
                    route = match.group(1)
                    if '<' not in route and route not in routes:  # Skip param routes
                        routes.append(route)
            except Exception:
                continue

        return routes[:4]  # Limit to 4 routes

    # Strategy 3: AI-Generated HTML Mockup
    async def _generate_html_mockup(self, api_key: str, max_screenshots: int = 4) -> List[str]:
        """Generate HTML mockup using Minimax M2 and render to PNG"""
        if not httpx or not async_playwright:
            print("httpx or Playwright not installed, skipping mockup generation")
            return []

        # Generate HTML with LLM
        html_content = await self._call_minimax_m2(api_key)
        if not html_content:
            return []

        # Save HTML file
        html_path = self.screenshots_dir / "mockup.html"
        html_path.write_text(html_content, encoding='utf-8')

        # Render to PNG with Playwright
        screenshot_path = self.screenshots_dir / "mockup.png"
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={'width': 1280, 'height': 800})
                await page.goto(f"file://{html_path.absolute()}")
                await page.screenshot(path=str(screenshot_path), full_page=False)
                await browser.close()

            return [str(screenshot_path)]
        except Exception as e:
            print(f"Error rendering mockup: {e}")
            return []

    async def _call_minimax_m2(self, api_key: str) -> Optional[str]:
        """Call Minimax M2 via OpenRouter to generate HTML mockup"""
        readme_content = self._read_readme_snippet()
        project_name = self.project_path.name

        prompt = f"""Create a beautiful single-file HTML mockup for this project:

Project: {project_name}
Description: {readme_content}

Requirements:
- Single HTML file with inline CSS and JavaScript
- Use Tailwind CDN for styling
- Modern, professional design
- Include project name as header
- Add 2-3 realistic UI sections based on project description
- Make it visually appealing with gradients and shadows
- Use placeholder images from picsum.photos if needed

Return ONLY the HTML code, no explanations."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://borg.tools",
                    },
                    json={
                        "model": "minimax/minimax-m2:free",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )
                response.raise_for_status()
                data = response.json()
                html = data['choices'][0]['message']['content']

                # Extract HTML if wrapped in code blocks
                html_match = re.search(r'```html\n(.*?)```', html, re.DOTALL)
                if html_match:
                    html = html_match.group(1)

                return html

        except Exception as e:
            print(f"Error calling Minimax M2: {e}")
            return None

    # Strategy 4: SVG Placeholder
    async def _generate_svg_placeholder(self) -> str:
        """Generate SVG placeholder with project name"""
        project_name = self.project_path.name
        emoji = self._get_project_emoji(project_name)

        svg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#grad)"/>
  <text x="600" y="280" font-family="Arial, sans-serif" font-size="72" fill="white" text-anchor="middle" font-weight="bold">
    {emoji}
  </text>
  <text x="600" y="370" font-family="Arial, sans-serif" font-size="48" fill="white" text-anchor="middle" font-weight="bold">
    {project_name}
  </text>
  <text x="600" y="420" font-family="Arial, sans-serif" font-size="24" fill="rgba(255,255,255,0.8)" text-anchor="middle">
    Project Screenshot Placeholder
  </text>
</svg>"""

        svg_path = self.screenshots_dir / "placeholder.svg"
        svg_path.write_text(svg_content, encoding='utf-8')
        return str(svg_path)

    def _get_project_emoji(self, project_name: str) -> str:
        """Get emoji based on project name keywords"""
        name_lower = project_name.lower()

        emoji_map = {
            'web': '🌐', 'api': '🔌', 'bot': '🤖', 'chat': '💬',
            'dashboard': '📊', 'game': '🎮', 'app': '📱', 'tool': '🛠️',
            'scanner': '🔍', 'parser': '📝', 'server': '🖥️', 'client': '💻',
            'database': '🗄️', 'auth': '🔐', 'crypto': '🔒', 'ai': '🧠',
            'ml': '🤖', 'data': '📊', 'analytics': '📈', 'monitor': '👁️',
            'test': '🧪', 'docs': '📚', 'ui': '🎨', 'ux': '✨'
        }

        for keyword, emoji in emoji_map.items():
            if keyword in name_lower:
                return emoji

        return '📦'  # Default

    # Helper methods
    def _find_readme(self) -> Optional[Path]:
        """Find README file in project"""
        for name in ['README.md', 'readme.md', 'Readme.md', 'README', 'readme']:
            readme = self.project_path / name
            if readme.exists():
                return readme
        return None

    def _read_readme_snippet(self, max_chars: int = 500) -> str:
        """Read snippet from README for context"""
        readme = self._find_readme()
        if not readme:
            return "No description available"

        try:
            content = readme.read_text(encoding='utf-8', errors='ignore')
            # Remove markdown formatting
            content = re.sub(r'[#*`\[\]()]', '', content)
            return content[:max_chars].strip()
        except Exception:
            return "No description available"

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped during scanning"""
        skip_dirs = {'.venv', 'node_modules', '.git', 'dist', 'build', '__pycache__', '.next', 'out'}
        return any(part in skip_dirs for part in file_path.parts)


# Public API
async def generate_screenshots(
    project_path: str,
    strategy: str = "auto",
    max_screenshots: int = 4,
    openrouter_api_key: Optional[str] = None
) -> List[str]:
    """
    Generate 3-4 screenshots for project

    Args:
        project_path: Absolute path to project directory
        strategy: Generation strategy (auto, extract, real, mock, placeholder)
        max_screenshots: Maximum number of screenshots to generate
        openrouter_api_key: API key for Minimax M2 (optional, for mock strategy)

    Returns:
        List of screenshot file paths (absolute paths)

    Examples:
        >>> screenshots = await generate_screenshots("/path/to/project")
        >>> screenshots = await generate_screenshots("/path/to/project", strategy="mock", openrouter_api_key="sk-...")
    """
    generator = ScreenshotGenerator(project_path)
    return await generator.generate(strategy, max_screenshots, openrouter_api_key)


# CLI interface for testing
async def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python screenshot_generator.py <project_path> [strategy] [api_key]")
        print("Strategies: auto, extract, real, mock, placeholder")
        sys.exit(1)

    project_path = sys.argv[1]
    strategy = sys.argv[2] if len(sys.argv) > 2 else "auto"
    api_key = sys.argv[3] if len(sys.argv) > 3 else os.getenv('OPENROUTER_API_KEY')

    print(f"Generating screenshots for: {project_path}")
    print(f"Strategy: {strategy}")

    screenshots = await generate_screenshots(project_path, strategy, 4, api_key)

    print(f"\nGenerated {len(screenshots)} screenshots:")
    for screenshot in screenshots:
        print(f"  - {screenshot}")


if __name__ == "__main__":
    asyncio.run(main())
