version 1.0

# Compare file md5sums
# Input type: File

task calculate_md5sum_optional {
	input {
		File? current_run_output
		File? validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		# Compare files
		echo "Comparing file md5sums"
		current_run_md5sum=$(md5sum ~{current_run_output} | cut -d ' ' -f 1)
		validated_output_md5sum=$(md5sum ~{validated_output} | cut -d ' ' -f 1)

		if [[ "$current_run_md5sum" != "$validated_output_md5sum" ]]; then
			err "File md5sums did not match:
				Expected md5sum: [$validated_output_md5sum]
				Current run md5sum: [$current_run_md5sum]"
			exit 1
		else
			# Error: Expected String instead of File?; for basename argument #1
			echo "File md5sums matched for file: [$(basename ~{current_run_output})]"
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
