from flask import Flask, render_template, redirect, url_for, flash
import os
import subprocess
import mail
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"

@app.route('/')
def index():
    # Read links from the relevant file
    try:
        with open("vuln_links.txt", "r") as f:
            vuln_links = f.readlines()  # Read all lines (URLs)
    except FileNotFoundError:
        vuln_links = []

    total_links = len(vuln_links)

    # You can also send this data to the template
    return render_template("index.html", total_links=total_links, vuln_links=vuln_links)

@app.route('/run-webcrawler', methods=['POST'])
def run_webcrawler():
    try:
        subprocess.run(['python3', 'webcrawler.py'], check=True)
        flash("Web Crawler executed successfully!", "success")
    except subprocess.CalledProcessError:
        flash("Failed to run Web Crawler!", "danger")
    return redirect(url_for('index'))

@app.route('/run-scraper', methods=['POST'])
def run_scraper():
    try:
        subprocess.run(['python3', 'scraper.py'], check=True)
        flash("Scraper executed successfully!", "success")
    except subprocess.CalledProcessError:
        flash("Failed to run Scraper!", "danger")
    return redirect(url_for('index'))

@app.route('/vuln-links')
def vuln_links():
    with open("vuln_links.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
    return render_template("vuln_links.html", lines=lines)

@app.route('/output-log')
def output_log():
    with open("output.txt", "r", encoding="utf-8") as f:
        content = f.read()
    return render_template("output_log.html", content=content)

@app.route('/show-vuln-links')
def show_vuln_links():
    # Read the vuln_links.txt or another file where links are stored
    try:
        with open("vuln_links.txt", "r") as f:
            vuln_links = f.readlines()  # Read all lines (URLs)
    except FileNotFoundError:
        vuln_links = []

    return render_template("show_vuln_links.html", vuln_links=vuln_links)

@app.route('/high-severity-links')
def high_severity_links(return_only=False):
    high_links = []

    try:
        with open("output.txt", "r") as f:
            lines = f.readlines()
            current_entry = []

            for line in lines:
                if line.strip() == "":
                    entry_text = " ".join(current_entry).lower()
                    severity_found = False

                    # Match numeric severity
                    num_match = re.search(r"severity[:\s]*([0-9]*\.?[0-9]+)", entry_text)
                    if num_match:
                        try:
                            score = float(num_match.group(1))
                            if score >= 7.0:
                                high_links.append("".join(current_entry))
                                severity_found = True
                        except ValueError:
                            pass

                    # Match keyword severity
                    if not severity_found:
                        if "severity: high" in entry_text or "severity: critical" in entry_text:
                            high_links.append("".join(current_entry))

                    current_entry = []

                else:
                    current_entry.append(line)

            # Handle last entry if not empty
            if current_entry:
                entry_text = " ".join(current_entry).lower()
                severity_found = False

                num_match = re.search(r"severity[:\s]*([0-9]*\.?[0-9]+)", entry_text)
                if num_match:
                    try:
                        score = float(num_match.group(1))
                        if score >= 7.0:
                            high_links.append("".join(current_entry))
                            severity_found = True
                    except ValueError:
                        pass

                if not severity_found:
                    if "severity: high" in entry_text or "severity: critical" in entry_text:
                        high_links.append("".join(current_entry))

    except FileNotFoundError:
        high_links = []

    if return_only:
        return high_links
    return render_template("high_severity_links.html", high_links=high_links)

@app.route('/send-high-severity-email')
def send_high_severity_email():
    try:
        mail.send_email()
        flash('✅ Email sent successfully!', 'success')
    except Exception as e:
        flash(f'❌ Failed to send email: {str(e)}', 'danger')
    return redirect(url_for('high_severity_links'))

if __name__ == '__main__':
    app.run(debug=True)
