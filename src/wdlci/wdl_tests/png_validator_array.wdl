version 1.0

# Check integrity of image file
# Input type: Array of PNG, JNG or MNG image files

task png_validator_array {
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

		while read -r file || [[ -n "$file" ]]; do
			if ! pngcheck "$file"; then
				err "Validated image file: [$(basename "$file")] is invalid"
				exit 1
			fi
		done < ~{write_lines(validated_output)}

		while read -r file || [[ -n "$file" ]]; do
			if ! pngcheck "$file"; then
				err "Current run image file: [$(basename "$file")] is invalid"
				exit 1
			else
				echo "Current run image file: [$(basename "$file")] is valid"
			fi
		done < ~{write_lines(current_run_output)}
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
