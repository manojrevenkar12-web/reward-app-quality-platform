import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm")
    kotlin("plugin.serialization")
    application
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

application {
    mainClass.set("com.rewardapp.backend.ApplicationKt")
}

val ktor = "3.0.3"

dependencies {
    implementation("io.ktor:ktor-server-core:$ktor")
    implementation("io.ktor:ktor-server-netty:$ktor")
    implementation("io.ktor:ktor-server-content-negotiation:$ktor")
    implementation("io.ktor:ktor-serialization-kotlinx-json:$ktor")
    implementation("org.slf4j:slf4j-simple:2.0.16")
    testImplementation("io.ktor:ktor-server-test-host:$ktor")
    testImplementation("au.com.dius.pact.provider:junit5:4.6.17")
    testImplementation("org.junit.jupiter:junit-jupiter:5.11.4")
    testImplementation(kotlin("test"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher:1.11.4")
}

// The provider is verified against the contract the app's consumer tests wrote.
tasks.test {
    useJUnitPlatform()
    dependsOn(":api-client:test")
    inputs.dir(rootProject.file("contracts/pacts"))
    systemProperty("pact.verifier.publishResults", "false")
}
