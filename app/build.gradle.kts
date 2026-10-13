plugins {
    id("com.android.application")
}

android {
    namespace = "net.bonstio.watchface.gshark"
    compileSdk = 35

    defaultConfig {
        applicationId = "net.bonstio.watchface.gshark"
        minSdk = 34
        targetSdk = 35
        versionCode = 4
        versionName = "1.3"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}

dependencies {
    // Watch Face Format uses system declarative rendering.
    // No runtime executable libraries required for WFF version 1+.
}
