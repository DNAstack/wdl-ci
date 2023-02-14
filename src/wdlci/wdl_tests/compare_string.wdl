version 1.0

# Compare strings
# Input type: String

task compare_string {
	input {
		String current_run_output
		String validated_output
	}

	Int disk_size = 10

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if [[ ~{current_run_output} != ~{validated_output} ]]; then
			err "Strings did not match:
				Expected output: [~{validated_output}]
				Current run output: [~{current_run_output}]"
			exit 1
		else
				echo "Strings matched [~{validated_output}]"
		fi
	>>>

	output {
		Int rc = read_int("rc")
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
