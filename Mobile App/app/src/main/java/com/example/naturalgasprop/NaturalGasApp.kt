package com.example.naturalgasprop

import android.app.Application
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class NaturalGasApp : Application() {
    override fun onCreate() {
        super.onCreate()
        // Initialize Chaquopy Python Runtime
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }
    }
}
