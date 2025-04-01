version 1.0

# Validate input HTML files
# Input type: HTML file

task html_validator {
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

		# Ignore flag specified because error: Element "head" is missing a required instance of child element "title".
		if ! html5validator ~{validated_output} --ignore head; then
			err "Validated HTML: [~{basename(validated_output)}] is invalid"
			exit 1
		else
			if ! html5validator ~{current_run_output} --ignore head; then
				err "Current run HTML: [~{basename(current_run_output)}] is invalid"
				exit 1
			else
				echo "Current run HTML: [~{basename(current_run_output)}] is valid"
			fi
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.1.0"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}