version 1.0

# Validate and compare input Array[Array[String]] types
# Input type: Array[Array[String]]

task validate_and_compare_pbsv_splits {
    input {
        Array[Array[String]] current_run_output
        Array[Array[String]] validated_output
    }

    Int disk_size = 10

    File current_lines_file = write_lines(flatten(current_run_output))
    File validated_lines_file = write_lines(flatten(validated_output))

    Array[String] current_lines = flatten(current_run_output)
    Array[String] validated_lines = flatten(validated_output)

    command <<<
        set -euo pipefail

        err() {
            message=$1
            echo -e "[ERROR] $message" >&2
        }

        # Compare the flattened arrays
        if ! diff -q "~{current_lines_file}" "~{validated_lines_file}"; then
            err "Flattened arrays are not identical. Differences found:
                    Expected output: [~{sep="," current_lines}]
                    Current run output: [~{sep="," validated_lines}]"
            exit 1
        else
            echo "Flattened arrays matched: ~{sep="," validated_lines}"
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