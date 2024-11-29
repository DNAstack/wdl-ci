version 1.0

# Compare float values
# Input type: Float

task compare_float {
		input {
			Float current_run_output
			Float validated_output
		}

		Int disk_size = 10

		command <<<
			set -euo pipefail

			err() {
				message=$1

				echo -e "[ERROR] $message" >&2
			}

			if [[ "~{current_run_output}" != "~{validated_output}" ]]; then
				err "Floats did not match:
					Expected output: [~{validated_output}]
					Current run output: [~{current_run_output}]"
				exit 1
			else
				echo "Floats matched [~{validated_output}]"
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
