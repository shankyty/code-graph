java_library(
    name = "my-lib",
    srcs = glob(["src/main/java/**/*.java"]),
    deps = [
        "//path/to/dep:lib",
        "@maven//:com_google_guava_guava",
    ],
)

java_test(
    name = "my-test",
    deps = [
        ":my-lib",
        "//test/dep:junit",
    ],
)
