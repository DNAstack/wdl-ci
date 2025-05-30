version 1.0

# Check empty lines
# Input type: File or GZ file

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

		if gzip -t ~{current_run_output} 2> /dev/null; then
			current_run_output_empty_lines_count=$(zgrep -c "^$" ~{current_run_output} || [[ $? == 1 ]])
			validated_output_empty_lines_count=$(zgrep -c "^$" ~{validated_output} || [[ $? == 1 ]])
		else
			current_run_output_empty_lines_count=$(grep -c "^$" ~{current_run_output} || [[ $? == 1 ]])
			validated_output_empty_lines_count=$(grep -c "^$" ~{validated_output} || [[ $? == 1 ]])
		fi

		if [[ "$validated_output_empty_lines_count" != 0 ]]; then
			err "Empty lines present in validated output: [~{basename(validated_output)}]. Count: [$validated_output_empty_lines_count]"
			exit 1
		fi

		if [[ "$current_run_output_empty_lines_count" != "$validated_output_empty_lines_count" ]]; then
			err "Empty lines present:
				Expected output: [$validated_output_empty_lines_count]
				Current run output: [$current_run_output_empty_lines_count]"
			exit 1
		else
			echo "No empty lines. Count: [$current_run_output_empty_lines_count]"
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
