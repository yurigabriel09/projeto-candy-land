plugins {
    id("com.android.application") version "9.5.1" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.4.21" apply false
    id("com.google.gms.google-services") version "4.5.0" apply false
}
val externalBuildRoot =
    file("C:/Users/theom/Documents/Theo/CandyLand_Project/DevBuilds/CandyLandMobile")

layout.buildDirectory.set(externalBuildRoot.resolve("root"))

subprojects {
    layout.buildDirectory.set(
        externalBuildRoot.resolve(name)
    )
}