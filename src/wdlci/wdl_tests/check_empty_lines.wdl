version 1.0

# Check empty lines
# Input type: File

task check_empty_lines {
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

		if gzip -t ~{current_run_output}; then
			current_run_output_empty_lines_count=$(zgrep -c "^$" ~{current_run_output})
			validated_output_empty_lines_count=$(zgrep -c "^$" ~{validated_output})
		else
			current_run_output_empty_lines_count=$(grep -c "^$" ~{current_run_output})
			validated_output_empty_lines_count=$(grep -c "^$" ~{validated_output})
		fi

		if [[ "$current_run_output_empty_lines_count" != "$validated_output_empty_lines_count" ]]; then
			err "Empty lines present:
				Expected output: [$validated_output_empty_lines_count]
				Current run output: [$current_run_output_empty_lines_count]"
			exit 1
		else
			echo "No empty lines. Count: [$validated_output_empty_lines_count]"
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
