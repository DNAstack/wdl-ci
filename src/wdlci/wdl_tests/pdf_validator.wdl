version 1.0

# Validate PDF file
# Input type: PDF file

task pdf_validator {
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

		if ! qpdf --check ~{validated_output}; then
			err "Validated PDF: [~{basename(validated_output)}] is invalid"
			exit 1
		else
			if ! qpdf --check ~{current_run_output}; then
				err "Current run PDF: [~{basename(current_run_output)}] is invalid"
				exit 1
			else
				echo "Current run PDF: [~{basename(current_run_output)}] passed QPDF validator"
			fi
		fi
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
