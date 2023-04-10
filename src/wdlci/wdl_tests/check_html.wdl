version 1.0

# Check input HTML files
# Input type: HTML file

task check_html {
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

		current_run_output_html_format_count=$(grep -c -e '<!DOCTYPE html>' -e '<' ~{current_run_output} || [[ $? == 1 ]])
		validated_output_html_format_count=$(grep -c -e '<!DOCTYPE html>' -e '<' ~{validated_output} || [[ $? == 1 ]])

		if [[ "$current_run_output_html_format_count" != "$validated_output_html_format_count" ]]; then
			err "Line count does not match when checking html format:
				Expected output: [$validated_output_html_format_count]
				Current run output: [$current_run_output_html_format_count]"
			exit 1
		else
			echo "Line count matches when checking html format. Count: [$current_run_output_html_format_count]"
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
