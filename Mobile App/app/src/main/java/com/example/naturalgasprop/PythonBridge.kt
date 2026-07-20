package com.example.naturalgasprop

import android.util.Log
import com.chaquo.python.Python
import org.json.JSONObject

object PythonBridge {
    private const val TAG = "PythonBridge"

    /**
     * Calls the calculate_properties_json function in android_bridge.py python module.
     * Takes input parameter JSON and returns output result JSON.
     */
    fun calculateProperties(jsonInput: String): String {
        return try {
            Log.d(TAG, "Calling python calculate_properties_json with: $jsonInput")
            val py = Python.getInstance()
            val module = py.getModule("android_bridge")
            val calculateFn = module.get("calculate_properties_json") ?: throw NullPointerException("calculate_properties_json function not found in android_bridge")
            val result = calculateFn.call(jsonInput)
            result.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error executing Python calculation", e)
            val errObj = JSONObject().apply {
                put("status", "error")
                put("error_message", e.localizedMessage ?: "Unknown error in Python execution bridge")
            }
            errObj.toString()
        }
    }

    /**
     * Calls the generate_pdf_report_json function in android_bridge.py python module.
     * Takes input parameter JSON and target file path, and returns status JSON.
     */
    fun generatePdfReport(jsonInput: String, outputPdfPath: String): String {
        return try {
            Log.d(TAG, "Calling python generate_pdf_report_json to path: $outputPdfPath")
            val py = Python.getInstance()
            val module = py.getModule("android_bridge")
            val generateFn = module.get("generate_pdf_report_json") ?: throw NullPointerException("generate_pdf_report_json function not found in android_bridge")
            val result = generateFn.call(jsonInput, outputPdfPath)
            result.toString()
        } catch (e: Exception) {
            Log.e(TAG, "Error generating PDF via Python", e)
            val errObj = JSONObject().apply {
                put("status", "error")
                put("error_message", e.localizedMessage ?: "Unknown error in PDF generation bridge")
            }
            errObj.toString()
        }
    }
}
