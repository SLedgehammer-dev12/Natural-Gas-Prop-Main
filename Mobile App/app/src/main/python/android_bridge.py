import json
import logging
import traceback
import math
from typing import Dict, Any

from natural_gas_main.models.gas_data import GasComponent, GasMixture
from natural_gas_main.models.calculator import ThermoCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AndroidBridge")

def clean_nan(obj):
    """Recursively converts NaN and Inf values to None for standard JSON serialization."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(x) for x in obj]
    return obj

def calculate_properties_json(input_json_str: str) -> str:
    """
    Receives input parameters in JSON format, performs thermodynamics calculations 
    using the ThermoCalculator engine, and returns a JSON response.
    """
    try:
        logger.info(f"Received calculation request: {input_json_str}")
        data = json.loads(input_json_str)
        
        # Build components
        components = []
        for comp in data.get("components", []):
            components.append(GasComponent(
                name=comp["name"],
                fraction=float(comp["fraction"])
            ))
            
        mixture = GasMixture(
            components=components,
            fraction_type=data.get("fraction_type", "molar")
        )
        
        # Initialize calculator
        calc = ThermoCalculator()
        
        # Extract parameters
        temp_k = float(data["temperature_k"])
        press_pa = float(data["pressure_pa"])
        backend = data.get("backend", "neqsim-gerg2008")
        volume_m3 = data.get("volume_m3")
        standard_T = data.get("standard_T", 288.15)
        standard_P = data.get("standard_P", 101325.0)
        standard_name = data.get("standard_name")
        
        # Run calculation with fallback
        result, used_backend = calc.calculate_with_fallback(
            mixture=mixture,
            temperature_k=temp_k,
            pressure_pa=press_pa,
            preferred_backend=backend,
            volume_m3=volume_m3,
            standard_T=standard_T,
            standard_P=standard_P,
            standard_name=standard_name
        )
        
        # Convert result model to dictionary (compatible with Pydantic v2/v1)
        result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
        result_dict["backend_used"] = used_backend
        
        # Clean up NaNs before JSON encoding
        clean_result = clean_nan(result_dict)
        
        return json.dumps({
            "status": "success",
            "result": clean_result
        })
        
    except Exception as e:
        logger.error(f"Error in calculate_properties_json: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error_message": str(e),
            "traceback": traceback.format_exc()
        })

def generate_pdf_report_json(input_json_str: str, output_pdf_path: str) -> str:
    """
    Runs thermodynamics calculations on the input JSON parameters, formats the result list,
    and writes a PDF report to output_pdf_path. Returns a status JSON.
    """
    try:
        logger.info(f"Received PDF generation request for path: {output_pdf_path}")
        data = json.loads(input_json_str)
        
        # Build components
        components = []
        gas_composition_tuples = []
        for comp in data.get("components", []):
            components.append(GasComponent(
                name=comp["name"],
                fraction=float(comp["fraction"])
            ))
            gas_composition_tuples.append((comp["name"], float(comp["fraction"])))
            
        mixture = GasMixture(
            components=components,
            fraction_type=data.get("fraction_type", "molar")
        )
        
        # Initialize calculator
        calc = ThermoCalculator()
        
        # Extract parameters
        temp_k = float(data["temperature_k"])
        press_pa = float(data["pressure_pa"])
        backend = data.get("backend", "neqsim-gerg2008")
        volume_m3 = data.get("volume_m3")
        standard_T = data.get("standard_T", 288.15)
        standard_P = data.get("standard_P", 101325.0)
        standard_name = data.get("standard_name")
        unit_system = data.get("unit_system", "SI")
        
        # Run calculation with fallback
        result, used_backend = calc.calculate_with_fallback(
            mixture=mixture,
            temperature_k=temp_k,
            pressure_pa=press_pa,
            preferred_backend=backend,
            volume_m3=volume_m3,
            standard_T=standard_T,
            standard_P=standard_P,
            standard_name=standard_name
        )
        
        # Prepare input params for report generator
        temp_unit_str = data.get("temp_unit_str", "C")
        press_unit_str = data.get("press_unit_str", "bar")
        temp_val_str = data.get("temp_val_str", str(temp_k))
        press_val_str = data.get("press_val_str", str(press_pa))
        
        input_params = {
            "temperature": f"{temp_val_str} {temp_unit_str}",
            "pressure": f"{press_val_str} {press_unit_str}",
            "backend": used_backend,
            "fraction_type": data.get("fraction_type", "molar"),
            "volume": str(volume_m3) if volume_m3 else ""
        }
        
        # Format results as list of tuples
        results_list = result.to_display_list(unit_system=unit_system)
        
        # Generate PDF report
        from natural_gas_main.utils.report_generator import ReportGenerator
        ReportGenerator.generate_pdf_report(
            input_params=input_params,
            results=results_list,
            gas_composition=gas_composition_tuples,
            file_path=output_pdf_path,
            plot_image_path=None # No phase envelope plot image on Android
        )
        
        return json.dumps({
            "status": "success",
            "pdf_path": output_pdf_path
        })
        
    except Exception as e:
        logger.error(f"Error in generate_pdf_report_json: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error_message": str(e),
            "traceback": traceback.format_exc()
        })

