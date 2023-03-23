version 1.0

# Check integrity of GZ file
# Input type: Array of GZ files

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

		while read -r file || [[ -n "$file" ]]; do
			if ! gzip -t "$file"; then
				err "Validated file: [$(basename "$file")] did not pass gzip check"
				exit 1
			fi
		done < ~{write_lines(validated_output)}
			
		while read -r file || [[ -n "$file" ]]; do
			if ! gzip -t "$file"; then
				err "Current run file: [$(basename "$file")] did not pass gzip check"
				exit 1
			else
				echo "Current run file: [$(basename "$file")] passed gzip check"
			fi
		done < ~{write_lines(current_run_output)}
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
