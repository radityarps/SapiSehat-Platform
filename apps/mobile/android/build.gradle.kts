import org.jetbrains.kotlin.gradle.dsl.JvmTarget
import org.jetbrains.kotlin.gradle.tasks.KotlinJvmCompile

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

subprojects {
    plugins.withId("com.android.library") {
        if (name == "camera_android_camerax") {
            // CameraX 1.6.0 exposes CallbackToFutureAdapter in its API jar, but
            // declares androidx.concurrent as a runtime dependency. With newer
            // AGP/Javac this class must also be present on the plugin compile
            // classpath.
            dependencies.add("implementation", "androidx.concurrent:concurrent-futures:1.1.0")
        }
    }
}

subprojects {
    tasks.withType<KotlinJvmCompile>().configureEach {
        compilerOptions {
            jvmTarget.set(
                if (project.name == "app" || project.name == "tflite_flutter") {
                    JvmTarget.JVM_11
                } else {
                    JvmTarget.JVM_17
                }
            )
        }
    }
    tasks.withType<JavaCompile>().configureEach {
        options.compilerArgs.add("-Xlint:-options")
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
