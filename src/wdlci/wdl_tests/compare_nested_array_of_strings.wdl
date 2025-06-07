version 1.0

# Check if two nested arrays of strings are identical by writing a TSV file of the data structure
# Input type: Array[Array[String]]

task compare_array_array_strings {
    input {
        Array[Array[String]] current_run_output
        Array[Array[String]] validated_output
    }

    Int disk_size = 10

    Int current_run_output_length = length(flatten(current_run_output))
    Int validated_output_length = length(flatten(validated_output))

    command <<<
        set -euo pipefail

        err() {
            message=$1
            echo -e "[ERROR] $message" >&2
        }

        if [[ ~{current_run_output_length} != ~{validated_output_length} ]]; then
            err "Nested array of strings have different flattened lengths.
                  Current run output length: [~{current_run_output_length}]
                  Validated output length: [~{validated_output_length}]"
            exit 1
        else
          if diff -q ~{write_tsv(current_run_output)} ~{write_tsv(validated_output)}; then
              echo "Nested array of strings are identical."
          else
              err "Nested array of strings are of the same length but are not identical."
              exit 1
          fi
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