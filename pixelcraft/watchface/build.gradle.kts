import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
}

// Release signing key lives outside git: keystore.properties next to settings.gradle.kts
// (storeFile, storePassword, keyAlias, keyPassword). Without it, release uses the debug key.
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

android {
    enableKotlin = false
    namespace = "com.pixelcraft.watchface"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.pixelcraft.watchface"
        // Weather data needs Watch Face Format v2 (Wear OS 5+).
        minSdk = 34
        targetSdk = 36
        versionCode = 2
        versionName = "1.1.0"
    }

    signingConfigs {
        if (keystoreProps.isNotEmpty()) {
            create("release") {
                storeFile = file(keystoreProps.getProperty("storeFile"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        debug {
            isMinifyEnabled = true
        }
        release {
            isMinifyEnabled = true
            // Resources are referenced only from watchface.xml; never shrink them.
            isShrinkResources = false
            signingConfig = signingConfigs.findByName("release") ?: signingConfigs.getByName("debug")
        }
    }
}
