version 1.0

# Check integrity of gz file
# Input type: Array of file.gz

task check_gzip_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	Int disk_size = ceil((size(current_run_output[0], "GB") * length(current_run_output)) + (size(validated_output[0], "GB") * length(validated_output)) + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		for file in ~{sep=' ' validated_output}; do
			if ! gzip -t "${file}"; then
				err "Validated file: ${file} did not pass gzip check"
				exit 1
			fi
		done

		for file in ~{sep=' ' current_run_output}; do
			if ! gzip -t "${file}"; then
				err "Current file: ${file} did not pass gzip check"
				exit 1
			else
				echo "Current file: ${file} passed gzip check"
			fi
		done
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
