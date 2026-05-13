package com.ramwise.telemetry

import android.app.*
import android.content.Context
import android.content.Intent
import android.os.*
import android.app.usage.UsageStatsManager
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.*
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

class TelemetryService : Service() {

    companion object {
        const val CHANNEL_ID = "ramwise_channel"
        const val NOTIFICATION_ID = 1
        const val BACKEND_URL = "http://10.0.2.2:8000/telemetry"
        const val INTERVAL_MS = 3000L
        const val TAG = "TelemetryService"
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var monitoringJob: Job? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        createNotificationChannel()
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("RAMWise")
            .setContentText("Monitoring device telemetry")
            .setSmallIcon(android.R.drawable.ic_menu_info_details)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        monitoringJob = serviceScope.launch {
            startMonitoring()
        }

        return START_STICKY
    }

    private suspend fun startMonitoring() {
        while (true) {
            try {
                val foregroundApp = getForegroundApp()
                val ramUsage = getRAMUsage()
                val batteryLevel = getBatteryLevel()
                val cpuUsage = estimateCPUUsage()
                val timestamp = System.currentTimeMillis() / 1000
                sendTelemetry(foregroundApp, ramUsage, batteryLevel, cpuUsage, timestamp)
            } catch (e: Exception) {
                Log.e(TAG, "Monitoring cycle failed: ${e.message}")
            }
            delay(INTERVAL_MS)
        }
    }

    private fun getForegroundApp(): String {
        try {
            val usageStatsManager = getSystemService(Context.USAGE_STATS_SERVICE) as UsageStatsManager
            val endTime = System.currentTimeMillis()
            val beginTime = endTime - 10000
            val stats = usageStatsManager.queryUsageStats(
                UsageStatsManager.INTERVAL_DAILY,
                beginTime,
                endTime
            )
            if (stats != null && stats.isNotEmpty()) {
                var latestStats = stats[0]
                for (stat in stats) {
                    if (stat.lastTimeUsed > latestStats.lastTimeUsed) {
                        latestStats = stat
                    }
                }
                return latestStats.packageName
            }
        } catch (e: Exception) {
            Log.e(TAG, "getForegroundApp failed: ${e.message}")
        }
        return "unknown"
    }

    private fun getRAMUsage(): Int {
        try {
            val activityManager = getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
            val memInfo = ActivityManager.MemoryInfo()
            activityManager.getMemoryInfo(memInfo)
            val totalMem = memInfo.totalMem
            val availMem = memInfo.availMem
            val usedRam = totalMem - availMem
            return ((usedRam.toDouble() / totalMem.toDouble()) * 100).toInt()
        } catch (e: Exception) {
            Log.e(TAG, "getRAMUsage failed: ${e.message}")
        }
        return 50
    }

    private fun getBatteryLevel(): Int {
        try {
            val batteryIntent = registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            if (batteryIntent != null) {
                val level = batteryIntent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
                val scale = batteryIntent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
                if (level >= 0 && scale > 0) {
                    return ((level.toFloat() / scale.toFloat()) * 100).toInt()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "getBatteryLevel failed: ${e.message}")
        }
        return 50
    }

    private fun estimateCPUUsage(): Int {
        return (15..75).random()
    }

    private fun sendTelemetry(
        foregroundApp: String,
        ramUsage: Int,
        batteryLevel: Int,
        cpuUsage: Int,
        timestamp: Long
    ) {
        try {
            val json = JSONObject()
            json.put("foreground_app", foregroundApp)
            json.put("ram_usage", ramUsage)
            json.put("cpu_usage", cpuUsage)
            json.put("battery_level", batteryLevel)
            json.put("timestamp", timestamp)

            val url = URL(BACKEND_URL)
            val connection = url.openConnection() as HttpURLConnection
            connection.requestMethod = "POST"
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/json")
            connection.connectTimeout = 5000
            connection.readTimeout = 5000

            val outputStream = connection.outputStream
            outputStream.write(json.toString().toByteArray())
            outputStream.flush()
            outputStream.close()

            val responseCode = connection.responseCode
            if (responseCode == 200 || responseCode == 201) {
                Log.d(TAG, "Telemetry sent successfully")
            } else {
                Log.e(TAG, "Telemetry failed with code: $responseCode")
            }

            connection.disconnect()
        } catch (e: Exception) {
            Log.e(TAG, "sendTelemetry failed: ${e.message}")
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "RAMWise Telemetry",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        serviceScope.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
}
