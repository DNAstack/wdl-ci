version 1.0

# Check if file is tab-delimited
# Input type: File

task check_tab_delimited {
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

		if awk '{exit !/\t/}' ~{validated_output}; then
			echo "Validated file is tab-delimited; continue"
			if awk '{exit !/\t/}' ~{current_run_output}; then
				echo "File is tab-delimited"
			else
				err "File is not tab-delimited"
				exit 1
			fi
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
