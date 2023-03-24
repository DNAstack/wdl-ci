version 1.0

# Compare file basenames
# Input type: Array of files

task compare_file_basename_array {
	input {
		Array[File] current_run_output
		Array[File] validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		# This is not an array, but rather a string with separated file names by space
		validated_basenames=$(for file in ~{sep=' ' validated_output}; do
				basename "$file"
			done)
		# Make it into an array
		validated_basenames=( "$validated_basenames" )

		current_run_basenames=$(for file in ~{sep=' ' current_run_output}; do
				basename "$file"
			done)
		current_run_basenames=( "$current_run_basenames" )

		# Validated and current should have the same amount of files
		length_array=${#validated_basenames[@]}

		for (( i=0; i<length_array; i++ )); do
			if [[ "${validated_basenames[$i]}" != "${current_run_basenames[$i]}" ]]; then
				err "File basenames did not match:
					Expected output: [${validated_basenames[$i]}]
					Current run output: [${current_run_basenames[$i]}]"
				exit 1
			else
				echo "File basenames matched [${validated_basenames[$i]}]"
			fi
		done
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
