version 1.0

# Check integrity of gz file
# Input type: file.gz

task check_gzip {
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

		if ! gzip -t ~{validated_output}; then
			err "Validated file: [~{basename(validated_output)}] did not pass gzip check"
			exit 1
		else
			if ! gzip -t ~{current_run_output}; then
				err "Current file: [~{basename(current_run_output)}] did not pass gzip check"
				exit 1
			else
				echo "Current file: [~{basename(current_run_output)}] passed gzip check"
			fi
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
