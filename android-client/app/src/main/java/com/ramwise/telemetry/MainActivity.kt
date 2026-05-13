package com.ramwise.telemetry

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        if (checkUsageStatsPermission()) {
            val serviceIntent = Intent(this, TelemetryService::class.java)
            ContextCompat.startForegroundService(this, serviceIntent)
        } else {
            Toast.makeText(
                this,
                "Please grant Usage Stats permission then reopen the app",
                Toast.LENGTH_LONG
            ).show()
            val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)
            startActivity(intent)
        }
    }

    private fun checkUsageStatsPermission(): Boolean {
        val appOps = getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.unsafeCheckOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            android.os.Process.myUid(),
            packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    override fun onDestroy() {
        super.onDestroy()
        stopService(Intent(this, TelemetryService::class.java))
    }
}
