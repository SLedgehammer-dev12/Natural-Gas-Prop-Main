"""
Data serialization utilities for saving and loading user inputs.

Provides JSON-based save/load functionality for gas composition and calculation parameters.
"""

import json
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# File extension for saved data
FILE_EXTENSION = ".ngp"
FILE_TYPE_NAME = "Natural Gas Properties"

# Current schema version
SCHEMA_VERSION = "1.0"


class DataSerializationError(Exception):
    """Error during data serialization or deserialization."""
    pass


def save_inputs_to_file(data: Dict[str, Any], filepath: str) -> None:
    """
    Save user inputs to a JSON file using an atomic write pattern.

    A temporary file is written first, then atomically renamed to the target
    path so that partial writes never corrupt an existing file.

    Args:
        data: Dictionary containing user inputs
        filepath: Path to save the file

    Raises:
        DataSerializationError: If save fails
    """
    try:
        if not filepath.endswith(FILE_EXTENSION):
            filepath += FILE_EXTENSION

        save_data = {
            **data,
            "version": SCHEMA_VERSION,
        }

        dir_path = os.path.dirname(filepath) or os.getcwd()
        fd, tmp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix="ngp_",
            dir=dir_path,
        )
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

        logger.info(f"Data saved to {filepath}")

    except DataSerializationError:
        raise
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        raise DataSerializationError(f"Kaydetme hatası: {e}")


def load_inputs_from_file(filepath: str) -> Dict[str, Any]:
    """
    Load user inputs from a JSON file.
    
    Args:
        filepath: Path to the file to load
        
    Returns:
        Dictionary containing user inputs
        
    Raises:
        DataSerializationError: If load fails or file is invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate schema version (major must match, minor can differ)
        file_version = data.get("version", "0.0")
        file_major = file_version.split(".")[0]
        our_major = SCHEMA_VERSION.split(".")[0]
        if file_major != our_major:
            raise DataSerializationError(
                f"Dosya şeması ({file_version}) bu uygulama ({SCHEMA_VERSION}) ile uyumlu değil. "
                f"Lütfen dosyayı güncel sürüm ile yeniden kaydedin."
            )
        
        logger.info(f"Data loaded from {filepath}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        raise DataSerializationError(f"Geçersiz dosya formatı: {e}")
    except FileNotFoundError:
        raise DataSerializationError("Dosya bulunamadı")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise DataSerializationError(f"Yükleme hatası: {e}")


def validate_loaded_data(data: Dict[str, Any]) -> bool:
    """
    Validate that loaded data has required fields and passes GasMixture
    Pydantic validation (component count, duplicate names, fraction ranges).

    Args:
        data: Loaded data dictionary
        
    Returns:
        True if data is valid, False otherwise
    """
    try:
        from natural_gas_main.models.gas_data import GasMixture, GasComponent

        required_fields = ["composition"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate composition structure
        composition = data.get("composition", [])
        if not isinstance(composition, list):
            return False
        if not composition:
            logger.warning("Composition list is empty")
            return False

        components = []
        for comp in composition:
            if not isinstance(comp, dict):
                return False
            if "name" not in comp or "fraction" not in comp:
                return False
            name = comp.get("name")
            fraction = comp.get("fraction")
            if not isinstance(name, str) or not name.strip():
                return False
            # Reject bools and non-numeric types
            if isinstance(fraction, bool) or not isinstance(fraction, (int, float)):
                return False
            components.append(GasComponent(name=name, fraction=fraction))

        fraction_type = data.get("fraction_type", "molar")
        if fraction_type not in ("molar", "mass"):
            return False

        # Run the full Pydantic GasMixture validation (count, duplicates, ranges)
        GasMixture(components=components, fraction_type=fraction_type)
        return True

    except Exception as e:
        logger.warning(f"Loaded data validation failed: {e}")
        return False
