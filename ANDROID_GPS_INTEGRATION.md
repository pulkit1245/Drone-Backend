# Android/Kotlin GPS Coordinates Integration

## 📡 POST /coordinates Endpoint

Send GPS location data from your Android/Kotlin app to the server.

### Endpoint URL
```
https://adahrs-ip-157-49-184-22.tunnelmole.net/coordinates
```

### Request Format

**Method**: POST  
**Content-Type**: application/json

**JSON Body**:
```json
{
    "latitude": 37.7749,
    "longitude": -122.4194,
    "timestamp": 1732713392000,
    "accuracy": 65.0,
    "altitude": 52.3,
    "speed": 1.5
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `latitude` | Double | ✅ Yes | Latitude in degrees (-90 to 90) |
| `longitude` | Double | ✅ Yes | Longitude in degrees (-180 to 180) |
| `timestamp` | Long | ✅ Yes | Unix timestamp in milliseconds |
| `accuracy` | Float | ❌ No | Horizontal accuracy in meters |
| `altitude` | Double | ❌ No | Altitude in meters |
| `speed` | Float | ❌ No | Speed in meters per second |

### Response

**Success (200)**:
```json
{
    "status": "ok",
    "received": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timestamp": 1732713392000,
        "timestamp_iso": "2024-11-27T13:16:32",
        "accuracy": 65.0,
        "altitude": 52.3,
        "speed": 1.5
    }
}
```

**Error (400)**:
```json
{
    "status": "error",
    "message": "latitude, longitude, and timestamp are required"
}
```

## 📱 Kotlin/Android Implementation

### Data Class (Already Defined)
```kotlin
data class LocationData(
    val latitude: Double,
    val longitude: Double,
    val timestamp: Long,
    val accuracy: Float? = null,
    val altitude: Double? = null,
    val speed: Float? = null
)
```

### Send Location to Server

```kotlin
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import kotlinx.coroutines.*

class LocationSender {
    private val client = OkHttpClient()
    private val serverUrl = "https://adahrs-ip-157-49-184-22.tunnelmole.net/coordinates"
    
    suspend fun sendLocation(locationData: LocationData): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                // Create JSON payload
                val json = JSONObject().apply {
                    put("latitude", locationData.latitude)
                    put("longitude", locationData.longitude)
                    put("timestamp", locationData.timestamp)
                    locationData.accuracy?.let { put("accuracy", it) }
                    locationData.altitude?.let { put("altitude", it) }
                    locationData.speed?.let { put("speed", it) }
                }
                
                // Create request
                val mediaType = "application/json; charset=utf-8".toMediaType()
                val body = json.toString().toRequestBody(mediaType)
                
                val request = Request.Builder()
                    .url(serverUrl)
                    .post(body)
                    .build()
                
                // Execute request
                val response = client.newCall(request).execute()
                val success = response.isSuccessful
                
                if (success) {
                    println("Location sent successfully: ${response.body?.string()}")
                } else {
                    println("Failed to send location: ${response.code}")
                }
                
                response.close()
                success
                
            } catch (e: Exception) {
                println("Error sending location: ${e.message}")
                false
            }
        }
    }
}
```

### Usage Example

```kotlin
// In your Activity or ViewModel
class MainActivity : AppCompatActivity() {
    private val locationSender = LocationSender()
    
    private fun onLocationUpdate(location: Location) {
        val locationData = LocationData(
            latitude = location.latitude,
            longitude = location.longitude,
            timestamp = System.currentTimeMillis(),
            accuracy = location.accuracy,
            altitude = location.altitude,
            speed = location.speed
        )
        
        // Send to server
        lifecycleScope.launch {
            val success = locationSender.sendLocation(locationData)
            if (success) {
                Log.d("GPS", "Location sent to server")
            }
        }
    }
}
```

### Continuous Location Updates

```kotlin
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager

class LocationTracker(private val context: Context) {
    private val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    private val locationSender = LocationSender()
    
    private val locationListener = object : LocationListener {
        override fun onLocationChanged(location: Location) {
            val locationData = LocationData(
                latitude = location.latitude,
                longitude = location.longitude,
                timestamp = System.currentTimeMillis(),
                accuracy = location.accuracy,
                altitude = location.altitude,
                speed = location.speed
            )
            
            // Send to server
            CoroutineScope(Dispatchers.IO).launch {
                locationSender.sendLocation(locationData)
            }
        }
    }
    
    fun startTracking() {
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            // Update every 1 second or 0 meters
            locationManager.requestLocationUpdates(
                LocationManager.GPS_PROVIDER,
                1000L,  // 1 second
                0f,     // 0 meters
                locationListener
            )
        }
    }
    
    fun stopTracking() {
        locationManager.removeUpdates(locationListener)
    }
}
```

## 🧪 Testing

### Test with cURL
```bash
curl -X POST https://adahrs-ip-157-49-184-22.tunnelmole.net/coordinates \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 37.7749,
    "longitude": -122.4194,
    "timestamp": 1732713392000,
    "accuracy": 65.0,
    "altitude": 52.3,
    "speed": 1.5
  }'
```

### View Received Data

**Server Console Output**:
```
[2024-11-27T13:16:32] GPS: lat=37.774900, lon=-122.419400, accuracy=±65.0m, altitude=52.3m, speed=1.50m/s, from=<your_ip>
```

**CSV Log File** (`coordinates_log.csv`):
```csv
timestamp_iso,timestamp_ms,latitude,longitude,accuracy,altitude,speed,client_ip
2024-11-27T13:16:32,1732713392000,37.7749,-122.4194,65.0,52.3,1.5,<your_ip>
```

## 📊 Monitor Incoming Coordinates

```bash
# Watch the log file update in real-time
tail -f coordinates_log.csv
```

## 🔐 Required Permissions (Android)

Add to `AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
```

## 📦 Dependencies (build.gradle)

```gradle
dependencies {
    implementation 'com.squareup.okhttp3:okhttp:4.11.0'
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
}
```

## ✅ Summary

Your Android app should:
1. Get GPS location using `LocationManager` or `FusedLocationProviderClient`
2. Create `LocationData` object with latitude, longitude, and timestamp
3. Convert to JSON and POST to `/coordinates` endpoint
4. Server will log and store the data in `coordinates_log.csv`

The endpoint is ready and working! 🎉
