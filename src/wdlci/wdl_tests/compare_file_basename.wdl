version 1.0

# Compare file basenames
# Input type: File

task compare_file_basename {
	input {
		File current_run_output
		File validated_output
	}

	String current_run_basename = basename(current_run_output)
	String validated_basename = basename(validated_output)

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		if [[ ~{current_run_basename} != ~{validated_basename} ]]; then
			err "File basenames did not match:
				Expected output: [~{validated_basename}]
				Current run output: [~{current_run_basename}]"
			exit 1
		else
			echo "File basenames matched [~{validated_basename}]"
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
