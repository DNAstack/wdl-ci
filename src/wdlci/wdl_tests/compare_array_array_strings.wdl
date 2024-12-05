version 1.0

# Check if two arrays of arrays of strings are identical by writing a TSV file of the data structure
# Input type: Array[Array[String]]

task compare_array_array_strings {
    input {
        Array[Array[String]] current_run_output
        Array[Array[String]] validated_output
    }

    Int disk_size = 10

    command <<<
        set -euo pipefail

        err() {
            message=$1
            echo -e "[ERROR] $message" >&2
        }

        if diff -q ~{write_tsv(current_run_output)} ~{write_tsv(validated_output)}; then
            echo "Nested array of strings are identical."
        else
            err "Nested array of strings not identical."
            exit 1
        fi
    >>>

    output {
    }

    runtime {
        docker: "ubuntu:xenial"
        cpu: 1
        memory: "3.75 GB"
        disk: disk_size + " GB"
        disks: "local-disk " + disk_size + " HDD"
        preemptible: 1
    }
}