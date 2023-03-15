version 1.0

# Check file contains only numeric values
# Input type: File

task check_numeric {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		#non_numeric_validated_output=$(sed 's/\t//g' ~{validated_output} | grep -cv '^[0-9]\+$')
		#non_numeric_current_output=$(sed 's/\t//g' ~{current_run_output} | grep -cv '^[0-9]\+$')

		if [[ $(sed 's/\t//g' ~{validated_output} | grep -cv '^[0-9]\+$') != $(sed 's/\t//g' ~{current_run_output} | grep -cv '^[0-9]\+$') ]]; then
			err "Current file: [~{basename(current_run_output)}] contains non-numeric values"
			exit 1
		else
			echo "Current file: [~{basename(current_run_output)}] contains only numeric values"
		fi
	>>>

	output {
		#Int rc = read_int("rc")
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
