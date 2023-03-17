version 1.0

# Check if array of files are tab-delimited
# Input type: Array of files

task check_tab_delimited_array {
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
			if ! awk '{exit !/\t/}' "${file}"; then
				err "Validated file: [${file}] is not tab-delimited"
				exit 1
			fi
		done

		for file in ~{sep=' ' current_run_output}; do
			if awk '{exit !/\t/}' "${file}"; then
				echo "File: [${file}] is tab-delimited"
			else
				err "File: [${file}] is not tab-delimited"
				exit 1
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