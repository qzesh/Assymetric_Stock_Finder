"""
Scheduled discovery runner for PythonAnywhere
Runs biweekly and sends email with results
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from discovery import run_discovery

def send_email_results(results, smtp_config):
    """Send discovery results via email."""
    
    # Build HTML email
    html = f"""
    <html>
        <body style="font-family: Arial; color: #333;">
            <h2>📊 Halal Asymmetric Stock Finder - Biweekly Update</h2>
            <p>Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>🏆 Top 5 Opportunities</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #667eea; color: white;">
                    <th style="padding: 10px;">Rank</th>
                    <th style="padding: 10px;">Ticker</th>
                    <th style="padding: 10px;">Score</th>
                    <th style="padding: 10px;">Pattern</th>
                    <th style="padding: 10px;">Track</th>
                    <th style="padding: 10px;">Signals</th>
                    <th style="padding: 10px;">Halal</th>
                </tr>
    """
    
    for candidate in results[:5]:
        pattern_color = '#28a745' if candidate['pattern'] == 'full' else '#ffc107' if candidate['pattern'] == 'partial' else '#dc3545'
        
        html += f"""
        <tr>
            <td style="padding: 10px;">{candidate['rank']}</td>
            <td style="padding: 10px;"><strong>{candidate['ticker']}</strong></td>
            <td style="padding: 10px;">{candidate['composite_score']:.2f}/3.0</td>
            <td style="padding: 10px; background-color: {pattern_color}; color: white;">{candidate['pattern'].upper()}</td>
            <td style="padding: 10px;">{candidate['track']}</td>
            <td style="padding: 10px;">{candidate['signal_raw']}/24</td>
            <td style="padding: 10px;">{candidate['halal_status'].upper()}</td>
        </tr>
        """
    
    html += """
            </table>
            
            <h3>📊 Summary</h3>
            <ul>
    """
    
    full_count = sum(1 for r in results if r['pattern'] == 'full')
    partial_count = sum(1 for r in results if r['pattern'] == 'partial')
    
    html += f"""
                <li>Total Candidates: {len(results)}</li>
                <li>Full Asymmetric Patterns: {full_count}</li>
                <li>Partial Asymmetric Patterns: {partial_count}</li>
            </ul>
            
            <p><strong>View full analysis:</strong> Open your Streamlit dashboard at:<br>
            http://localhost:8502</p>
            
            <hr>
            <p style="color: #888; font-size: 12px;">
            This is an automated email from Halal Asymmetric Stock Finder
            </p>
        </body>
    </html>
    """
    
    # Prepare email
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"🏆 Halal Stock Finder - Biweekly Update ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = smtp_config['from_email']
    msg['To'] = smtp_config['to_email']
    
    msg.attach(MIMEText(html, 'html'))
    
    # Send
    try:
        with smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port']) as server:
            server.starttls()
            server.login(smtp_config['email'], smtp_config['password'])
            server.send_message(msg)
        
        print(f"✓ Email sent to {smtp_config['to_email']}")
        return True
    except Exception as e:
        print(f"✗ Email failed: {str(e)}")
        return False


def is_scheduled_day():
    """
    Check if today is a scheduled biweekly day.
    
    Scheduled days: 15th and 28th of every month
    
    Returns: True if discovery should run, False otherwise
    """
    today = datetime.now().day
    
    # Fixed biweekly dates: 15th and 28th
    scheduled_days = [15, 28]
    
    if today not in scheduled_days:
        print(f"Not a scheduled discovery day (today is {today}/{datetime.now().month}) - skipping")
        return False
    
    print(f"Scheduled discovery day confirmed ({today}/{datetime.now().month}) - proceeding")
    return True


def main():
    """Run scheduled discovery and send results."""
    
    print(f"\n{'='*60}")
    print(f"🚀 Scheduled Discovery Task")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # Check if today is a scheduled day (biweekly logic)
    if not is_scheduled_day():
        return
    
    # Run discovery
    try:
        results = run_discovery()
        
        if not results:
            print("❌ Discovery returned no results")
            return
        
        print(f"\n✓ Discovery completed: {len(results)} candidates found")
        
        # Load email config from environment
        smtp_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': os.environ.get('EMAIL_USER'),
            'password': os.environ.get('EMAIL_PASSWORD'),
            'from_email': os.environ.get('EMAIL_USER'),
            'to_email': os.environ.get('RECIPIENT_EMAIL')
        }
        
        # Validate config
        if not all(smtp_config.values()):
            print("⚠️  Email config incomplete. Set environment variables:")
            print("   - EMAIL_USER")
            print("   - EMAIL_PASSWORD")
            print("   - RECIPIENT_EMAIL")
        else:
            # Send email
            send_email_results(results, smtp_config)
        
        print("\n✓ Scheduled discovery completed successfully")
        
    except Exception as e:
        print(f"❌ Error during discovery: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
