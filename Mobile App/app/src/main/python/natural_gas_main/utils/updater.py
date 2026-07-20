"""
Update checker utility.

Handles checking for updates from remote GitHub repository.
"""

import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
from typing import Tuple, Optional, Dict, Any
from packaging import version

from natural_gas_main.config.settings import config


class UpdateChecker:
    """Checks for application updates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_version = config.APP_VERSION
        self.update_url = config.UPDATE_CHECK_URL
    
    def check_for_updates(self) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Check if a new version is available.

        Returns:
            Tuple of (is_update_available, update_info_dict, status_message).
            status_message is None on success, or an error description on failure.
        """
        try:
            self.logger.info(f"Checking for updates from: {self.update_url}")

            with urllib.request.urlopen(self.update_url, timeout=5) as response:
                if response.status != 200:
                    msg = f"Sunucu yanıtı: {response.status}"
                    self.logger.warning(f"Update check failed: {msg}")
                    return False, None, msg

                data = json.loads(response.read().decode("utf-8"))
                remote_version = data.get("version")
                if not remote_version:
                    return False, None, "Sürüm bilgisi okunamadı."

                if version.parse(remote_version) > version.parse(self.current_version):
                    self.logger.info(
                        f"New version found: {remote_version} (Current: {self.current_version})"
                    )
                    return True, data, None

                self.logger.info("Application is up to date")
                return False, None, "Program güncel."

        except urllib.error.URLError as e:
            msg = "İnternet bağlantısı yok veya sunucuya erişilemiyor."
            self.logger.warning(f"Network error checking updates: {e}")
            return False, None, msg
        except Exception as e:
            msg = f"Güncelleme kontrolü başarısız: {e}"
            self.logger.error(msg, exc_info=True)
            return False, None, msg

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Validate that a URL points to GitHub (defense-in-depth)."""
        if not url:
            return False
        try:
            parsed = urllib.parse.urlparse(url)
            return parsed.netloc in ("github.com", "www.github.com")
        except Exception:
            return False

    def open_download_page(self, url: str = None):
        """Open the download/repo page in browser (only allows GitHub URLs)."""
        target_url = url or config.REPO_URL
        if target_url and not self._validate_url(target_url):
            self.logger.warning(f"Blocked non-GitHub URL: {target_url}")
            target_url = config.REPO_URL
        webbrowser.open(target_url)
