version 1.0

workflow hello {
    input {
        String name = "world"
    }

    call say_hello {
        input:
            name = name
    }

    output {
        File greeting = say_hello.greeting
    }
}

task say_hello {
    input {
        String name
    }

    command <<<
        set -euo pipefail
        echo "Hello, ~{name}!" > greeting.txt
    >>>

    output {
        File greeting = "greeting.txt"
    }

    runtime {
        docker: "ubuntu:22.04"
    }
}
