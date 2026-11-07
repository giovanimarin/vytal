package org.vytal.smokefixture

import android.app.Activity
import android.os.Bundle
import android.widget.TextView
import androidx.health.connect.client.HealthConnectClient
import androidx.health.connect.client.records.StepsRecord
import androidx.health.connect.client.records.metadata.Metadata
import kotlinx.coroutines.*
import java.time.Instant
import java.time.ZoneOffset

// Uses the real emulator Health Connect database; never pretends to be Garmin.
class MainActivity : Activity() {
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val status = TextView(this)
        setContentView(status)
        status.text = "Writing synthetic Health Connect steps"
        scope.launch {
            try {
                val end = Instant.now().minusSeconds(60)
                HealthConnectClient.getOrCreate(this@MainActivity).insertRecords(listOf(
                    StepsRecord(startTime = end.minusSeconds(600), startZoneOffset = ZoneOffset.UTC,
                        endTime = end, endZoneOffset = ZoneOffset.UTC, count = 123,
                        metadata = Metadata.manualEntry(clientRecordId = "vytal-synthetic-smoke", clientRecordVersion = 1))
                ))
                status.text = "SYNTHETIC_STEPS_INSERTED"
            } catch (error: Exception) { status.text = "FIXTURE_FAILED: ${error.message}" }
        }
    }
    override fun onDestroy() { scope.cancel(); super.onDestroy() }
}
