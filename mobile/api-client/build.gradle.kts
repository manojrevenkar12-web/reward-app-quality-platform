import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm")
    kotlin("plugin.serialization")
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    testImplementation("au.com.dius.pact.consumer:junit5:4.6.17")
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.11.4")
}

// The consumer tests write the contract the backend is verified against.
tasks.test {
    useJUnitPlatform()
    systemProperty("pact.rootDir", rootProject.file("contracts/pacts").absolutePath)
    outputs.dir(rootProject.file("contracts/pacts"))
}
